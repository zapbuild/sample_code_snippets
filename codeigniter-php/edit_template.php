
<!-- Use this page to edit, preview and save your card ---> 
 <script type="text/javascript">
  // Access this URL to preview your card 
   const Card_Review = "<?php echo base_url()?>previewCard?card=<?php echo encrypt_url($data->id)?>";
   // Redirection to the 'confirmation' page 
   const Redirect    = "<?php echo base_url()?>confirmation?card=<?php echo encrypt_url($data->id)?>";
 </script>
 <section id="location" class="parallax">
  <div class="container">
    <div class="row">
      <!-- Going back to previous page -->
      <div class="col-md-2 col-sm-10" style="margin-top: 23px;">
        <a href="<?php echo base_url()?>templates?detail=<?php echo encrypt_url($data->subcate_id)?>" class="btn btn-sm btn-warning">Back</a>
     </div>

      <div class="col-md-offset-2 col-md-10 col-sm-offset-1 col-sm-10 text-center">
          <div class="wow fadeInUp section-title" data-wow-delay="0.6s" style="margin-top: -50px;">
            <!-- Table details are being fetched by passing table name and ID, using common helper -->
            <h3 style="color: #A9537B"><?php $layout   = get_details('tbl_layout','','id',$data->id,'status',1);
                     $template = get_details('tbl_templates','','id',$layout->temp_id,'status',1);
                     $subcate  = get_details('tbl_card_subcategory','','id',$layout->subcate_id,'status',1);
                     echo  $subcate->sub_card_name. ':-' .$template->template_name ?></h3>
                     <hr style="border:1px solid black;">
          </div>
      </div>
    </div>
    <div class="clearfix"></div>
     <input type="hidden" id="edit_page" value="1">
     <form  id="save-card-information">
      <!-- Validating if data exists on front card-face -->
     <?php if((!empty($data->input_layout1)) && (!empty($data->temp_layout1))) {?>
    <div class="row" id="Front-card" >
    <div class="col-md-6 col-sm-6">   
    <div> <?php echo $data->input_layout1?></div>
    <div class="TextBoxContainer" class="form-group"></div> 
    </div>
      <div class="col-md-6 col-sm-6">
        <div id="Front-card-detail"> <?php echo $data->temp_layout1?></div> 
     </div>
   </div>
  <?php }?>
  <!-- Validating if data exists on rear card-face -->
     <?php if((!empty($data->input_layout2)) && (!empty($data->temp_layout2))) {?>
     <div class="row" id="back-card" style="display:none;">
    <div class="col-md-6 col-sm-6">
    <div> <?php echo $data->input_layout2?></div>
    <div class="TextBoxContainer" class="form-group"></div> 
    </div>
      <div class="col-md-6 col-sm-6">
        <div id="Back-card-detail"><?php echo $data->temp_layout2?></div> 
     </div>
    </div>
    <?php }?>
     <div class="row">
      <div class="col-md-6"> 
        <input type="hidden" value="<?php echo $data->backside ?>" id="backsidecheck">
      </div>
      <div class="col-md-6" style="float:right;margin-top:40px;">
        <!-- Buttons to toggle between card-faces(these buttons will appear only when back card-face is visible) -->
        <?php if((!empty($data->input_layout2)) && (!empty($data->temp_layout2))) {?>
        <button class="btn btn-success" type="button" onclick="card_hide_show('front')">Edit Front Site</button>
        <button class="btn btn-info"  type="button" onclick="card_hide_show('back')">Edit Back Site</button>
        <?php }?>
       </div>
     </div>
      </form>
      <!-- Creating card pop-up box -->
    <div class="popup" id="popup-1">
         <div class="overlay"></div>
         <div class="content">
           <div class="close-btn" onclick="closedPopup()">&times;</div> 
             <center><span style="font-size:x-large;font-weight:700;">Your Card Preview</span> </center>
             <hr style="border:1px solid #e6e6e6">
             <span style="float:left">
              View:<button class="Preview" type="button" onclick="popupdata('front-view')" id="front-view">Front View
              </button>
              <?php if( ($data->backside == 1) && ($data->temp_layout2)){?>
               |<button type="button" class="Preview" onclick="popupdata('back-view')" id="back-view">Back View</button>|
               <button class="Preview" type="button" onclick="popupdata('both-view')" id="both-view">Both View</button>
                <?php }?>
              </span><br><br><br>
             <div class="row">
               <div class="col-md-2 col-sm-2"></div>
               <div id="front-view-show" class="col-md-8 col-sm-8"></div>
               <?php if(!empty($data->temp_layout2) && $data->backside == 1){?>
               <div id="back-view-show" class="col-md-8 col-sm-8" style="display: none;">
               </div>
               <?php }?>
               <div class="col-md-2 col-sm-2"></div>
               </div>
               <div class="row" id="both-view-show" style="display: none;">
               <div class="col-md-1 col-sm-1"></div> 
               <div id="front-view-show-card" class="col-md-5 col-sm-5"></div>
                <?php if(!empty($data->temp_layout2) && $data->backside == 1){?>
              <div id="back-view-show-card" class="col-md-5 col-sm-5"></div>
              <?php } ?>
              <div class="col-md-1 col-sm-1"></div> 
             </div>
           </div>
        </div>
        <!-- Pop-up box ends here -->
        <div class="row" style="margin-top: -34px;">
         <!--  <div class="col-md-6"></div> -->
          <div class="col-md-6">
            <!-- Creating 'preview' and 'next' buttons -->
        <button type="button" style="" class="btn btn-md btn-success" onclick="togglePopup()">Preview Card</button>
           <button type="button" style="width: 130px;" value="<?php echo encrypt_url($data->id)?>" class="btn btn-md btn-primary" onclick="GoForReview(this)" id="GoForReview">Next</button>
        </div>
       </div>
      </div>
</section>
