const Fairs = require('../../models/admin/fairs');
const Stall = require('../../models/vendor/stalls');
const { check, validationResult } = require('express-validator');
const _ = require('underscore');
const config = require('../../configs/config');
const appointments = require('../common/appointments');
let moment = require('moment');
module.exports = {
    index: async (req, res) => {
        let sortBy = { 'createdAt': 'desc' }
        let populateFields = [{
            path: 'created_by', select: { '_id': 1, 'role': 1, 'first_name': 1, 'last_name': 1 }
        }, {
            path: 'category_id', select: { '_id': 1, 'name': 1, },
        }, {
            path: 'billboards',
            populate:{
                path: 'location'
            }
        }, {
            path: 'stalls', //select: { '_id': 1, 'name': 1, },
            populate: {
                path: 'vendor_id',
                select: { '_id': 1, 'first_name': 1, 'last_name': 1, 'email': 1, 'company': 1 },
                populate: {
                    path: 'country_id',
                    select: { 'name': 1, 'iso2': 1 }
                }
            }
        }]
        let options = {
            sort: sortBy,
            page: 1,
            limit: 50, //config.perPage,
            populate: populateFields
        }
              
        let conditions = { "is_deleted": false };
        if (req.query.page != undefined && parseInt(req.query.page)) {
            options.page = req.query.page;
        }
        if (req.query.limit != undefined && parseInt(req.query.limit)) {
            options.limit = req.query.limit;
        }
        if (req.query.sort != undefined && req.query.sort.length > 0) {
            options.sort = {}
            options.sort[req.query.sort] = req.query.sort_order
        }
        if (req.query.status != undefined && req.query.status.length > 0) {
            conditions.status = req.query.status;
        }
        if (req.query.category_id != undefined && req.query.category_id.length > 0) {
            conditions.category_id = req.query.category_id;
        }
        if (req.query.is_featured != undefined && req.query.is_featured.length > 0) {
            conditions.is_featured = req.query.is_featured;
        }
        if (req.query.from_date != undefined && req.query.from_date.length > 0 && req.query.to_date != undefined && req.query.to_date.length > 0) {
            console.log(req.query.from_date, req.query.from_date)
            let from_date = req.query.from_date  //new Date(req.query.from_date).toDateString()   
            let to_date = req.query.to_date //new Date(req.query.to_date).toDateString()
            console.log(from_date, to_date)
            conditions.$and = [
                {
                    $or: [{ "start_date": { '$lte': to_date } }, { "end_date": { '$lte': to_date } }]
                }, {
                    "end_date": { '$gte': from_date }
                }
            ];
        }
        if (req.query.condition_type != undefined && req.query.condition_type.length > 0) {
            let now = moment().toDate();
            console.log(now)
            switch (req.query.condition_type) {
                case 'All':
                    if (req.query.name != undefined && req.query.name.length > 0) {
                        conditions.$and = [{
                            'name': { $regex: '.*' + req.query.name.trim() + '.*', '$options': 'i' }
                        }]
                    }
                    break;
                case 'Active':
                    if (req.query.name != undefined && req.query.name.length > 0) {
                        conditions.$and = [                          
                            { $and: [{ "end_date": { '$gte': moment().startOf('day') } }, { "end_date": { '$gte': moment().startOf('day') } }] },
                            { $and: [{ 'name': { $regex: '.*' + req.query.name.trim() + '.*', '$options': 'i' } }] }
                        ]
                    } else {
                        conditions.$or = [{ "end_date": { '$gte': moment().startOf('day') } }, { "end_date": { '$gte': moment().startOf('day') } }];
                       
                    }
            }
        }
        if (req.query.export != undefined && req.query.export.length > 0) {
            const fields = [
                {
                    label: 'Fair',
                    value: 'name'
                },
                {
                    label: 'Start Date',
                    value: 'start_date_str'
                },
                {
                    label: 'End Date',
                    value: 'end_date_str'
                },
                {
                    label: 'Registration Start Date',
                    value: 'registration_start_date_str'
                },
                {
                    label: 'Appointment Start Date',
                    value: 'appointment_start_date_str'
                },
                {
                    label: 'Category',
                    value: 'category_id.name_str'
                },
       
                {
                    label: 'No of Stalls',
                    value: 'stall_capacity'
                },
                {
                    label: 'Status',
                    value: 'status_str'
                }
            ];
            let allFairs = await Fairs.find(conditions).sort(sortBy).populate({ path: 'created_by', select: { '_id': 1, 'role': 1, 'first_name': 1, 'last_name': 1 } }).populate({ path: 'category_id', select: { '_id': 1, 'name': 1 } }).populate({ path: 'billboards',populate:{path: 'location'} });;
            let dateFormat = config.dateFormat;
            switch (req.query.export) {
                case 'csv':
                    let updatedFairs = [];
                    await allFairs.forEach((fair, i) => {
                        updatedFairs[i] = allFairs[i];
                        if (allFairs[i]['status'] === 1 && moment(allFairs[i]['end_date']) < moment().startOf('day')) {
                            updatedFairs[i].status_str = "Completed";
                        } else if (allFairs[i]['status'] === 0 || moment(allFairs[i]['end_date']) < moment().toDate()) {
                            updatedFairs[i].status_str = "Inactive";
                        } else {
                            updatedFairs[i].status_str = "Active";
                        }
                        if (updatedFairs[i].category_id) {
                            updatedFairs[i].category_id.name_str = updatedFairs[i].category_id.name;
                        } else {
                            updatedFairs[i]['category_id'] = {};
                            updatedFairs[i]['category_id']['name_str'] = "NA";
                        }
                        updatedFairs[i].start_date_str = moment(allFairs[i]['start_date']).format(dateFormat);
                        updatedFairs[i].end_date_str = moment(allFairs[i]['end_date']).format(dateFormat);
                        updatedFairs[i].registration_start_date_str = moment(allFairs[i]['registration_start_date']).format(dateFormat);
                        updatedFairs[i].appointment_start_date_str = moment(allFairs[i]['appointment_start_date']).format(dateFormat);
                    });
                    return commonService.csvDownload(req, res, 'fairs.csv', fields, updatedFairs);
                    break;
                case 'pdf':
                    let randomstring = require("randomstring");
                    let dir = 'uploads/reports';
                    let fileName = 'report_' + moment().format('DDMMYYhmmss') + '_' + randomstring.generate(7) + '.pdf';
                    return res.render('../pdf/fairs/fairs.ejs', {
                        data: allFairs,
                        fields: fields,
                        moment: moment,
                        dateFormat: dateFormat,
                    }, function (err, html) {
                        if (!err) {
                            return commonService.pdfDownload(req, res, fileName, dir, html);
                        } else {
                            logService.log('error', err);
                            return commonService.sendCustomResult(req, res, 'SERVER_ERROR', 'COULD_NOT_EXPORT');
                        }
                    })
                    break;
            }
        }
        // console.log(JSON.stringify(conditions, null, 4));
        try {
            if (options.limit) {
                let allFairs = await Fairs.paginate(conditions, options);
                commonService.sendCustomResult(req, res, 'SUCCESS', 'FAIR_FOUND_SUCCESSFULLY', commonService.paginateData(allFairs));
            } else {
                let allFairs = await Fairs.find(conditions).populate(populateFields).sort(sortBy);
                commonService.sendCustomResult(req, res, 'SUCCESS', 'FAIR_FOUND_SUCCESSFULLY', allFairs);
            }
        } catch (error) {
            logService.log('error', error);
            commonService.sendCustomResult(req, res, 'SERVER_ERROR', 'FAIRS_NOT_FOUND');
        }
    },
    status: async (req, res) => {
        const errors = validationResult(req);
        if (!errors.isEmpty()) {
            return commonService.sendCustomResult(req, res, 'INVALID_REQUEST', 'VALIDATION_ERROR', { errors: errors.array() });
        }
        let data = req.body;
        try {
            let userFound = await Fairs.findOne({ _id: data.id });
            if (!userFound) {
                return commonService.sendCustomResult(req, res, 'NOT_FOUND', 'USER_NOT_FOUND');
            }
            let status = config.userStatus.INACTIVE;
            if (userFound.status !== config.userStatus.ACTIVE) {
                status = config.userStatus.ACTIVE;
            }
            userFound.status = status;
            let userUpdated = await userFound.save();
            if (userUpdated) {
                return commonService.sendCustomResult(req, res, 'SUCCESS', 'USER_STATUS_UPDATED');
            } else {
                return commonService.sendCustomResult(req, res, 'SERVER_ERROR', 'USER_STATUS_NOT_UPDATED');
            }
        } catch (error) {
            logService.log('error', error);
            commonService.sendCustomResult(req, res, 'SERVER_ERROR', 'USER_STATUS_NOT_UPDATED');
        }
    },
    add: async (req, res) => {
        let data = req.body;
        const errors = validationResult(req);
        if (!errors.isEmpty()) {
            return commonService.sendCustomResult(req, res, 'INVALID_REQUEST', 'VALIDATION_ERROR', { errors: errors.array() });
        }
        try {
       
            if (req.files && req.files.floor_plan && req.files.floor_plan[0]) {
                Object.assign(data, { floor_plan: req.files.floor_plan[0].filename })
                commonService.uploadFileToS3(config.fairPublicUrl, req.files.floor_plan[0].filename, config.fairAssetsUrl)
            } else {
                Object.assign(data, { floor_plan: "" })
            }
            if (req.files && req.files.banner && req.files.banner[0]) {
                Object.assign(data, { banner: req.files.banner[0].filename })
                commonService.uploadFileToS3(config.fairPublicUrl, req.files.banner[0].filename, config.fairAssetsUrl)
            } else {
                Object.assign(data, { banner: "" })
            }
            if (req.files && req.files.background_image && req.files.background_image[0]) {
                Object.assign(data, { background_image: req.files.background_image[0].filename })
                commonService.uploadFileToS3(config.fairPublicUrl, req.files.background_image[0].filename, config.fairAssetsUrl)
            } else {
                Object.assign(data, { background_image: "" })
            }
       
            if
                (
                moment(data.start_date) < moment().startOf('day') ||
                moment(data.end_date) < moment().startOf('day') ||
                moment(data.registration_start_date) < moment().startOf('day') ||
                moment(data.appointment_start_date) < moment().startOf('day')
            ) {
                return commonService.sendCustomResult(req, res, 'SERVER_ERROR', 'DATE_GREATER_THAN_TODAY');
            }
            if (!(data.end_date >= data.start_date)) {
                return commonService.sendCustomResult(req, res, 'SERVER_ERROR', 'VALID_END_DATE');
            }
            if (!(data.registration_start_date <= data.start_date)) {
                return commonService.sendCustomResult(req, res, 'SERVER_ERROR', 'VALID_REGISTRATION_START_DATE');
            }
            if (!(data.appointment_start_date <= data.start_date)) {
                return commonService.sendCustomResult(req, res, 'SERVER_ERROR', 'VALID_APPOINTMENT_START_DATE');
            }
            if (data.category_id === '') {
                delete data.category_id
            }
            if (data.country === '') {
                delete data.country
            }
     
            if (parseInt(data.no_of_stands_to_show) > parseInt(data.stall_capacity)) {
                return commonService.sendCustomResult(req, res, 'SERVER_ERROR', 'TOTAL_STALLS_SHOULD_MORE_OR_EQUAL_TO_STALLS_TO_SHOW');
            }
            if(data.seller_price && (parseFloat(data.seller_price) < 0.5 || isNaN(parseFloat(data.seller_price)) )){
                return commonService.sendCustomResult(req, res, 'SERVER_ERROR', 'INVALID_AMOUNT');
            }
            if(data.buyer_price 
                && (
                    parseFloat(data.buyer_price) < 0 
                    || isNaN(parseFloat(data.buyer_price)) 
                    || (parseFloat(data.buyer_price) < 0.5 && parseFloat(data.buyer_price) > 0)
                    )){
                return commonService.sendCustomResult(req, res, 'SERVER_ERROR', 'INVALID_AMOUNT');
            }
            let show_all_buyers = false;
            if(data.show_all_buyers == true){
                show_all_buyers = data.show_all_buyers
            }
            Fairs.findOne({ url: (req.body.url) })
                .then(async function (fairFound) {
                    if (fairFound) {
                        return commonService.sendCustomResult(req, res, 'RECORD_ALREADY_EXISTS', 'SAME_NAME_FAIR_ALREADY_EXISTS');
                    } else {
                        let newFair = await Fairs.create({
                            name: data.name,
                            created_by: req.user.id,
                            category_id: data.category_id,
                            start_date: data.start_date,
                            end_date: data.end_date,
                            registration_start_date: data.registration_start_date,
                            appointment_start_date: data.appointment_start_date,
                            floor_plan: data.floor_plan,                          
                            stall_capacity: data.stall_capacity,
                            address: data.address,
                            country: data.country,
                            url: data.url,
                            status: data.status,
                            banner: data.banner,
                            buyer_price: data.buyer_price,
                            seller_price: data.seller_price,
                            background_image: data.background_image,
                            currency: data.currency,
                            is_featured: data.is_featured,
                            description: data.description,
                            no_of_stands_to_show: data.no_of_stands_to_show,
                            show_all_buyers : show_all_buyers
                         
                        });
                      
                        return newFair;
                    }
                })
                .then(async function (fairCreated) {
                    let data = {
                        fair_id: fairCreated._id,
                        start_date: fairCreated.start_date,
                        end_date: fairCreated.end_date
                    }
                    let dome = 1
                    let stallsArray = await commonService.divideInsertStalls(fairCreated._id, fairCreated.stall_capacity, dome);
                    let stalls = await Stall.create(stallsArray);
                    let stallIds = _.pluck(stalls, "_id");
                    await Fairs.findByIdAndUpdate({ _id: fairCreated._id }, { $push: { stalls: { $each: stallIds } } }, { new: true });
                    let slotsCreated = await appointments.createSlots(data)
                    let resData = Object.assign({}, { fair: fairCreated }, { slots: slotsCreated })
                    return commonService.sendCustomResult(req, res, 'RECORD_CREATED', 'FAIR_CREATED', resData);
                });
        } catch (error) {
            logService.log('error', error);
            commonService.sendCustomResult(req, res, 'SERVER_ERROR', 'FAIR_NOT_CREATED');
        }
    },
    edit: async (req, res) => {
        let data = req.body;
        try {
            if (!req.params.id) {
                return commonService.sendCustomResult(req, res, 'INVALID_REQUEST', 'INVALID_ID');
            }
            if (!req.params.id.match(/^[0-9a-fA-F]{24}$/)) {
                return commonService.sendCustomResult(req, res, 'INVALID_REQUEST', 'INVALID_ID');
            }
            let fairFound = await Fairs.findOne({ _id: req.params.id }).populate({ path: 'stalls' })
            if (!fairFound) {
                return commonService.sendCustomResult(req, res, 'NOT_FOUND', 'FAIR_NOT_FOUND');
            }
            if (req.files && req.files.floor_plan && req.files.floor_plan[0]) {
                Object.assign(data, { floor_plan: req.files.floor_plan[0].filename })
                commonService.uploadFileToS3(config.fairPublicUrl, req.files.floor_plan[0].filename, config.fairAssetsUrl)  
            }
            if (req.files && req.files.banner && req.files.banner[0]) {
                Object.assign(data, { banner: req.files.banner[0].filename })
                commonService.uploadFileToS3(config.fairPublicUrl, req.files.banner[0].filename, config.fairAssetsUrl)
            }
            if (req.files && req.files.background_image && req.files.background_image[0]) {
                Object.assign(data, { background_image: req.files.background_image[0].filename })
                commonService.uploadFileToS3(config.fairPublicUrl, req.files.background_image[0].filename, config.fairAssetsUrl)
           
            }
            if (parseInt(data.no_of_stands_to_show) > parseInt(data.stall_capacity)) {
                return commonService.sendCustomResult(req, res, 'SERVER_ERROR', 'TOTAL_STALLS_SHOULD_MORE_OR_EQUAL_TO_STALLS_TO_SHOW');
            }
            if(data.seller_price && (parseFloat(data.seller_price) < 0.5 || isNaN(parseFloat(data.seller_price)) )){
                return commonService.sendCustomResult(req, res, 'SERVER_ERROR', 'INVALID_AMOUNT');
            }
            if(data.buyer_price 
                && (
                    parseFloat(data.buyer_price) < 0 
                    || isNaN(parseFloat(data.buyer_price)) 
                    || (parseFloat(data.buyer_price) < 0.5 && parseFloat(data.buyer_price) > 0)
                    )){
                return commonService.sendCustomResult(req, res, 'SERVER_ERROR', 'INVALID_AMOUNT');
            }
            delete data.end_date
            delete data.start_date 
            if(data.registration_start_date || data.appointment_start_date ){
                if (!(moment(data.registration_start_date).toISOString() <= moment(fairFound.start_date).toISOString())) {
                    return commonService.sendCustomResult(req, res, 'SERVER_ERROR', 'VALID_REGISTRATION_START_DATE');
                }
                if (!(moment(data.appointment_start_date).toISOString() <= moment(fairFound.start_date).toISOString())) {
                    return commonService.sendCustomResult(req, res, 'SERVER_ERROR', 'VALID_APPOINTMENT_START_DATE');
                }
            }
            if (data.category_id === '') {
                delete data.category_id
            }
            if (data.country === '') {
                delete data.country
            }

          
            let newDomes =  1; //fairFound.domes;
            let newStalls = fairFound.stall_capacity;
            let shouldUpdate = false;
    
            if (data.stall_capacity > fairFound.stall_capacity) {
                newStalls = data.stall_capacity;
                shouldUpdate = true
            }
            if (shouldUpdate) {
                let newStallsArray = await commonService.divideInsertStalls(fairFound._id, newStalls, newDomes);
                console.log("stallsArray", newStallsArray)
                let oldStalls = fairFound.stalls;
                let toUpdateStall = [];
                _.map(newStallsArray, function (stall) {
                    let oldStallUpdate = _.find(oldStalls, function (oldStall) {
                        return stall.position == oldStall.position;
                    });
                    if (oldStallUpdate) {                  
                    } else {
                        let insertOne = {
                            "insertOne": {
                                "document": stall
                            }
                        }
                        toUpdateStall.push(insertOne);
                    }
                })
                let updatedFair = await Stall.bulkWrite(toUpdateStall);
                let stallIds = _.pluck(updatedFair.insertedIds, "_id");
                await Fairs.findByIdAndUpdate({ _id: fairFound._id }, { $addToSet: { stalls: { $each: stallIds } } }, { new: true });
            }
           
            Fairs.findOne({ $and: [{ "url": { '$eq': data.url } }, { "_id": { '$ne': req.params.id } }] })
                .then(async function (fairFound) {
                    if (fairFound) {
                        return commonService.sendCustomResult(req, res, 'RECORD_ALREADY_EXISTS', 'SAME_NAME_FAIR_ALREADY_EXISTS');
                    } else {
                        let fairUpdated = await Fairs.findOneAndUpdate({ _id: req.params.id }, data, { new: true }).populate({ path: 'created_by', select: { '_id': 1, 'role': 1, 'first_name': 1, 'last_name': 1 } }).populate({ path: 'category_id', select: { '_id': 1, 'name': 1 } }).populate({ path: 'country', select: { '_id': 1, 'name': 1 } }).populate({ path: 'billboards',populate:{path: 'location'} })
                        if (fairUpdated) {
                            return commonService.sendCustomResult(req, res, 'SUCCESS', 'FAIR_DETAILS_UPDATED', { fair: fairUpdated });
                        } else {
                            return commonService.sendCustomResult(req, res, 'SERVER_ERROR', 'FAIR_DETAILS_NOT_UPDATED');
                        }
                    }
                });
        } catch (error) {
            logService.log('error', error);
            commonService.sendCustomResult(req, res, 'SERVER_ERROR', 'FAIR_DETAILS_NOT_UPDATED');
        }
    },
    details: async (req, res) => {
        try {
            let conditions = {}
            if (req.params.id.match(/^[0-9a-fA-F]{24}$/)) {
                conditions.$and = [{ "_id": { '$eq': req.params.id } }, { "is_deleted": { '$eq': false } }]
            } else {
                conditions.url = req.params.id
            }
            let fairFound = await Fairs.findOne(conditions).populate({ path: 'created_by', select: { '_id': 1, 'role': 1, 'first_name': 1, 'last_name': 1 } }).populate({ path: 'category_id', select: { '_id': 1, 'name': 1 } }).populate({ path: 'country', select: { '_id': 1, 'name': 1 } }).populate({ path: 'billboards',populate:{path: 'location'} });
            if (fairFound) {
                return commonService.sendCustomResult(req, res, 'SUCCESS', 'FAIR_FOUND', { fair: fairFound });
            } else {
                return commonService.sendCustomResult(req, res, 'NOT_FOUND', 'FAIR_NOT_FOUND');
            }
        } catch (error) {
            logService.log('error', error);
            commonService.sendCustomResult(req, res, 'SERVER_ERROR', 'FAIR_NOT_FOUND');
        }
    },
    delete: async (req, res) => {
        try {
            let isFairFound = await Fairs.findOne({ _id: req.params.id, is_deleted: false });
            if (isFairFound) {
                let FairUpdated = await Fairs.findByIdAndUpdate({ _id: req.params.id }, { is_deleted: true }, { new: true });
                if (FairUpdated) {
                    return commonService.sendCustomResult(req, res, 'SUCCESS', 'FAIR_DELETED', {});
                } else {
                    return commonService.sendCustomResult(req, res, 'SERVER_ERROR', 'FAIR_NOT_DELETED');
                }
            } else {
                commonService.sendCustomResult(req, res, 'SERVER_ERROR', 'FAIR_NOT_FOUND');
            }
        } catch (error) {
            logService.log('error', error);
            commonService.sendCustomResult(req, res, 'SERVER_ERROR', 'FAIR_NOT_FOUND');
        }
    },
}