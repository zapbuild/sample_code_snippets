const jwt = require('jsonwebtoken');
const config = require('../configs/config');
const Email = require('email-templates');
const nodemailer = require("nodemailer");
var moment = require('moment');
var momenttz = require('moment-timezone');
var fs = require('fs');
var path = require('path');
const https = require('https');
const { Parser } = require('json2csv');
var wkhtmltopdf = require('wkhtmltopdf');
const AWS = require('aws-sdk');
module.exports = {
  codeList: { SUCCESS: 200, RECORD_CREATED: 201, BAD_REQUEST: 400, AUTH_ERROR: 401, FORBIDDEN: 403, NOT_FOUND: 404, INVALID_REQUEST: 405, BLOCKED_CONTENT: 410, RECORD_ALREADY_EXISTS: 409, SERVER_ERROR: 500 },
  sendCustomResult: (req, res, status_code, message, data) => {
    var result = {
      status: {
        code: module.exports.codeList[status_code],
        message: i18n.__(message)
      }
    };
    if (typeof data !== 'undefined') {
      result.data = data;
    } else {
      result.data = {};
    }
    return res.json(result);
  },
  paginateData: (data) => {
    var result = {
      records: data.docs,
      page: data.page,
      total_pages: data.totalPages,
      page_records: (data.docs).length,
      total_records: data.totalDocs,
    }
    return result;
  },
  jwtIssue: (payload, tokenSecret, expiryTime) => {
    return jwt.sign(
      payload,
      tokenSecret, // Token Secret that we sign it with
      {
        expiresIn: expiryTime // Token Expire time 
      }
    );
  },
  jwtVerify: (token, tokenSecret, callback) => {
    return jwt.verify(
      token, // The token to be verified
      tokenSecret, // Same token we used to sign
      {}, // No Option, 
      callback //Pass errors or decoded token to callback
    );
  },
  jwtDecode: (token) => {
    return jwt.decode(token);
  },
  generateOTP: (length) => {
    var digits = '0123456789';
    let OTP = '';
    for (let i = 0; i < length; i++) {
      OTP += digits[Math.floor(Math.random() * 10)];
    }
    return OTP;
  },
  sendEmail: async (templateName, toEmail, subject, data) => {
    let transporter = nodemailer.createTransport(config.mailerSettings);
    let dateFormat = "Do MMMM YYYY";
    let timeFormat = 'dddd HH:mm';
    const email = new Email({
      message: {
        from: config.fromEmail
      },
      preview: false,
      send: true,
      transport: transporter,
      views: {
        options: {
          extension: 'ejs'
        }
      }
    });
    data.assets_url = config.assetsPublicUrl // Assets url for images in all emails
    data.moment = momenttz;
    data.mom = moment ;
    if (data.first_name != undefined && data.first_name) {
      data.first_name = data.first_name;
    }
    email.send({
      template: templateName,
      message: {
        to: toEmail
      },
      locals: {
        subject: subject,
        data: data,
        moment: momenttz,
        mom : moment,
        dateFormat: dateFormat,
        timeFormat:timeFormat,
        config : config
      }
    }).then((result) => {
      console.log('Email subject: ', subject, ' Sent to: ', toEmail);
    }).catch((error) => {
      logService.log('error', error);
    });
  },
  deleteFile: async (filePath) => {
    try {
      return fs.unlinkSync(filePath);
    } catch (error) {
      logService.log('error', error);
      return false;
    }
  },
  otpExiryTime: () => {
    return Date.now() + config.otpExpiryTime
  },
  copyFile: async (source, destination) => {
    try {
      if (fs.existsSync(source)) {
        if (!fs.existsSync(path.dirname(path.dirname(destination)))) { // if parent destination directory not exists then create new
          fs.mkdirSync(path.dirname(path.dirname(destination)),{recursive: true})
          if (!fs.existsSync(path.dirname(destination))) {               // if destination directory not exists then create new
            fs.mkdirSync(path.dirname(destination),{recursive: true})
          }
        } else {
          if (!fs.existsSync(path.dirname(destination))) {
            fs.mkdirSync(path.dirname(destination),{recursive: true})  // if parent directory exists but destination directory not exists then create new
          }
        }
        fs.copyFileSync(source,destination);
        // fs.createReadStream(source).pipe(fs.createWriteStream(destination))
        return true;
      }
    } catch (error) {
      logService.log('error', error);
      return false;
    }
  },
  convertUnitsToMeter: async (value, unit) => {
    var finalValue = value
    switch (unit) {
      case 'miles':
        finalValue = parseInt(value * 1609.34)
        break;
      case 'km':
      default:
        finalValue = parseInt(value * 1000)
        break;
    }
    return finalValue
  },
  uploadFileToS3: async (folderName, fileName, dirPath, sizeArr) => {
    return new Promise(function (resolve, reject) {
      AWS.config.update({
        accessKeyId: process.env.AWS_ACCESS_KEY_ID,
        secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
        region: "us-east-2",
      });
      var s3 = new AWS.S3();
      var images = [];
      var i = 1;
      fs.readFile(dirPath + fileName, function (err, data) {
        console.log("err", err)
        if (err) { throw err }
        images.push(folderName + fileName);
        var params = {
          Bucket: 'directlyitaly',
          'Key': folderName + fileName,
          'Body': data,
          'ACL': 'public-read'
        };
        s3.upload(params, function (err, data) {
          console.log('S3 upload err, data, ', err, data)
           resolve(images);
          i = i + 1;
        })
      });
    });
  },
  __deleteImagesFromS3: function (bucketFolder, sizeArr, image) {
    return new Promise(function (resolve, reject) {
      var AWS = require('aws-sdk');
      AWS.config.update({
        accessKeyId: config.awsApi,
        secretAccessKey: config.awsSecret
      });
      var s3 = new AWS.S3();
      var deleteImage = [];
      var imageName = image;
      deleteImage.push({ Key: bucketFolder + '/' + imageName });
      var params = {
        Bucket: config.awsBucket,
        Delete: { /* required */
          Objects: deleteImage,
          Quiet: true
        },
      };
      s3.deleteObjects(params, function (err, data) {
        if (err) {
          console.log(err, err.stack);
          resolve(false)
        } // an error occurred
        else {
          resolve(true)
        }
      });
    });
  },
  csvDownload: (req, res, fileName, fields, data) => {
    let opts = { fields };
    try {
      let parser = new Parser(opts);
      let csv = parser.parse(data);
      res.header('Content-Type', 'text/csv');
      res.attachment(fileName);
      return res.send(csv);
    } catch (err) {
      logService.log('error', err);
      commonService.sendCustomResult(req, res, 'SERVER_ERROR', 'COULD_NOT_EXPORT');
    }
  },
  pdfDownload: (req, res, fileName, dir, html) => {
    try {
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir);
      }
      var wkhOptions = {
        output: dir + '/' + fileName,
        pageSize: 'A4',
        encoding: 'utf-8',
        orientation: 'landscape'
      };
      wkhtmltopdf(html, wkhOptions, function (err, stream) {
        var stream = fs.createReadStream(dir + '/' + fileName);
        stream.pipe(res.attachment(fileName));
        var had_error = false;
        stream.on('error', function (err) {
          had_error = true;
          logService.log('error', err);
          commonService.sendCustomResult(req, res, 'SERVER_ERROR', 'COULD_NOT_EXPORT');
        });
        stream.on('close', function () {
          if (!had_error) {
            fs.unlink(dir + '/' + fileName, function (err) {
              if (err) {
                logService.log('error', err);
                commonService.sendCustomResult(req, res, 'SERVER_ERROR', 'COULD_NOT_EXPORT');
              }
            });
          }
        });
      });
    } catch (err) {
      logService.log('error', err);
      commonService.sendCustomResult(req, res, 'SERVER_ERROR', 'COULD_NOT_EXPORT');
    }
  },


  checkNotificationType: (notificationType) => {
    if(
      notificationType === 'requested_appointment' ||
      notificationType === 'accepted_request_vendor' ||
      notificationType === 'rejected_request_vendor' ||
      notificationType === 'entered' ||
      notificationType === 'visited' ||
      notificationType === 'requested_chat' ||
      notificationType === 'left_stall' ||
      notificationType === 'purchased' ||
      notificationType === 'called' ||
      notificationType === 'downloaded_docs' ||
      notificationType === 'went_without_purchase' ||
      notificationType === 'sent_alert' ||
      notificationType === 'ordered' ||
      notificationType === 'message_missed'
    ){
      return 'vendor'
    }else if(
      notificationType === 'accepted_request' ||
      notificationType === 'rejected_request' ||
      notificationType === 'requested_appointment_vendor'
      ) {
        return 'buyer'
      }
  },
}