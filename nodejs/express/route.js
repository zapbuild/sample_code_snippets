const express = require('express')
const router = express.Router()
const billBoardController = require('../../controllers/admin/billboards')
const isAuthorized = require('../../middlewares/isAuthorized')
const isAdmin = require('../../middlewares/isAdmin')
const acl = require('../../middlewares/checkAcl')
const accepted_extensions = ['image/jpeg','image/jpg','image/png'];
var multer  = require('multer')
var fs = require('fs');
var randomstring = require('randomstring');
var config = require('../../configs/config')
var storage = multer.diskStorage({
    limits: { 
        fileSize: 5 * 1024 * 1024,  // 5 MB upload limit
    },    
    destination: function (req, file, cb) {
      if(accepted_extensions.indexOf(file.mimetype) > -1){
        var path = config.billBoardAssetsUrl;
        if (!fs.existsSync(path)) {
          fs.mkdirSync(path);
        }
        cb(null, path)
      } else {
        return cb(new Error('Invalid image format'));
      }
    },
    filename: function (req, file, cb) {
      var extension = file.originalname.split('.').pop();     
      var uuid = randomstring.generate(10) + '_' + Date.now() + "."+ extension;
      cb(null, uuid)
    }
  })
  
  var upload = multer({ storage: storage })
/**
* @swagger
* /admin/billboards:
*   post:
*     tags:
*       - BillBoard
*     description: Add BillBoard
*     security:              
*       - Bearer: []   
*     consumes:
*       - application/x-www-form-urlencoded
*     produces:
*       - application/json
*     parameters:
*       - name: name
*         description: Name of billboard
*         in: formData
*         required: true
*         type: string
*       - name: location
*         description: Location Id
*         in: formData
*         required: true
*         type: string
*       - name: fair_id
*         description: Fair Id for billboard 
*         in: formData
*         required: true
*         type: string
*       - name: image
*         description: image
*         in: formData
*         required: true
*         type: file
*     responses:
*       200:
*         description: BillBoard created successfully
*       400:
*         description: Bad request
*       401:
*         description: Invalid billboard details. Please try again
*       500:
*         description: Something went wrong. Server Error    
*
*/
router.post('/', [isAuthorized,acl,upload.array('image',1)], billBoardController.add);
/**
* @swagger
* /admin/billboards/{id}:
*   put:
*     tags:
*       - BillBoard
*     description: Add BillBoard
*     security:              
*       - Bearer: []   
*     consumes:
*       - application/x-www-form-urlencoded
*     produces:
*       - application/json
*     parameters:
*       - name: id
*         description: BillBoard Id 
*         in: path
*         required: true
*         type: string
*       - name: name
*         description: Name of billboard
*         in: formData
*         required: true
*         type: string
*       - name: location
*         description: Location Id
*         in: formData
*         required: true
*         type: string
*       - name: fair_id
*         description: Fair Id for billboard 
*         in: formData
*         required: true
*         type: string
*       - name: image
*         description: image
*         in: formData
*         required: false
*         type: file
*     responses:
*       200:
*         description: BillBoard created successfully
*       400:
*         description: Bad request
*       401:
*         description: Invalid billboard details. Please try again
*       500:
*         description: Something went wrong. Server Error    
*
*/
router.put('/:id', [isAuthorized,acl,upload.array('image',1)], billBoardController.edit);
/**
* @swagger
* /admin/billboards:
*   get:
*     tags:
*       - BillBoard
*     description: BillBoards listing
*     security:              
*       - Bearer: []     
*     produces:
*       - application/json
*     parameters:
*       - name: name
*         description: Name of the billboard
*         in: query
*         required: false
*         type: string
*       - name: fair_id
*         description: fair id
*         in: query
*         required: false
*         type: string
*       - name: page
*         description: Page number
*         in: query
*         required: false
*         type: number
*       - name: limit
*         description: Limit number of records per page
*         in: query
*         required: false
*         type: number
*       - name: sort
*         description: Sort column
*         in: query
*         required: false
*         type: string
*       - name: sort_order
*         description: sorting order
*         in: query
*         required: false
*         enum: 
*           - ASC
*           - DESC
*     responses:
*       200:
*         description: billboards found successfully
*       400:
*         description: Bad request
*       404:
*         description: User not found
*       500:
*         description: Something went wrong. Server Error    
*
*/
router.get('/', [isAuthorized,acl], billBoardController.index);
/**
* @swagger
* /admin/billboards/{id}:
*   get:
*     tags:
*       - BillBoard
*     description: BillBoard details
*     produces:
*       - application/json
*     security:              
*       - Bearer: []   
*     parameters:
*       - name: id
*         description: BillBoard id
*         in: path
*         required: true
*         type: string
*     responses:
*       200:
*         description: BillBoard found successfully
*       400:
*         description: Bad request
*       404:
*         description: User not found
*       500:
*         description: Something went wrong. Server Error    
*
*/
router.get('/:id', [isAuthorized,acl], billBoardController.details);
/**
* @swagger
* /admin/billboards/{id}:
*   delete:
*     tags:
*       - BillBoard
*     description: Delete BillBoard
*     security:              
*       - Bearer: []  
*     consumes:
*       - application/json
*     produces:
*       - application/json
*     parameters:
*       - name: id
*         description: Billboard  Id
*         in: path
*         required: true
*         type: string
*     responses:
*       200:
*         description: Billboard deleted successfully
*       400:
*         description: Bad request
*       500:
*         description: Something went wrong. Server Error    
*
*/
router.delete('/:id', [isAuthorized,acl], billBoardController.delete);
module.exports.router = router;
module.exports = router;