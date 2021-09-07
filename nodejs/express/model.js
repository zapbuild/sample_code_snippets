// stall information created by admin
var mongoose = require("mongoose"); 
const mongoosePaginate = require("mongoose-paginate-v2");
var Schema = mongoose.Schema;
var config = require('../../configs/config');
var docsSchema = new Schema({
    brochure: { type: String, },
    product_manuals: { type: Array, default: [] },
    offer_leaflet: { type: String, },
    flyer: { type: String, },
    service_module: { type: String }
});
let  billboardSchema = new Schema({
    fair_id: { type: mongoose.ObjectId, ref: 'Fair' },
    created_by: { type: mongoose.ObjectId, ref: 'User' },
    name: { type: String, required: true },
    location: { type: mongoose.ObjectId, ref: 'Location' },
    image: { type: String, required: false },
    status: { type: Boolean, default: 1 },// 0 inactive, 1 active
    is_deleted: { type: Boolean, default: false },
}, {
    timestamps: true
});
mongoosePaginate.paginate.options = {
    limit: 10
};
billboardSchema.plugin(mongoosePaginate);
billboardSchema.methods.toJSON = billboardInformation;
billboardSchema.methods.filterUserData = billboardInformation;
function billboardInformation() {
    var obj = this.toObject();
    // change in the urls if any
    return obj;
}
// case of populate
billboardSchema.virtual('image_url').get(function () {
    let imageName = this.image;
    if(this.image !== undefined  && this.image !== ''){
        return config.mediaHostUrl+'/'+ config.billBoardPublicUrl + imageName		
    } else {
        return '';	
    }
});
billboardSchema.set('toObject', { virtuals: true });
billboardSchema.pre("save", function (next) {
    if (this.isNew) {
    }
    next();
});
module.exports = mongoose.model("Billboard", billboardSchema);