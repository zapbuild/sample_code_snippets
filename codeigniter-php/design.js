
//Toggling between front & rear card-faces
function card_hide_show(value){
      if(value == 'front'){
           $('#Front-card').css('display','block')
           $('#back-card').css('display','none')
        }else if(value == 'back'){
            $('#Front-card').css('display','none')
            $('#back-card').css('display','block')
          }else{
             $('#Front-card').css('display','block')
             $('#back-card').css('display','none')
        }
 }   


//Adding & Removing text fields
$(function () {
    $("#btnAdd").bind("click", function () {
        var div = $("<div />");
        div.html(GetDynamicTextBox(""));
        $(".TextBoxContainer").append(div);
    });
    $("#btnGet").bind("click", function () {
        var values = "";
        $("input[name=DynamicTextBox]").each(function () {
            values += $(this).val() + "\n";
        });
        alert(values);
    });
    $("body").on("click", ".remove", function () {
        $(this).closest("div").remove();
    });
});

function GetDynamicTextBox(value) {
    return '<input name = "DynamicTextBox"  class="form-control "type="text" placeholder="Enter Value" value = "' + value + '" />&nbsp;' +
            '<input type="button" value="Remove" class="remove btn btn-sm" />'
           
}



//Fetching data onto cards(Front side) By Ankuresh
$(function() {
    $('input').keyup(function(){
         var inputname = $(this).attr('name');
         var value = $(this).val();
          if(value.length >0){
             $('#'+inputname).html('');
             $('#'+inputname).html(value);
             window.localStorage.setItem(inputname,value);     
           }
      })
   
})
 // On page load, the data stored in local storage is fetched onto card-face and the text-boxes as well
$("form#save-card-information :input").each(function(){
 var input = $(this);
  $.each(input.serializeArray(), function(i, field) {
    if($('input[name='+field.name+']').val() !="" || getSavedValue(field.name) ){
    $('input[name='+field.name+']').val(getSavedValue(field.name));
    $('#'+field.name).html(getSavedValue(field.name)).css('cursor','pointer');
    $('#'+field.name).draggable();  
      }  
    });
});

// Creating card-preview pop-up box
function togglePopup(){
     document.getElementById("popup-1").classList.toggle("active"); 
      $('#Front-card').css('display','none');
      var div_content=document.getElementById('Front-card-detail').innerHTML;
      document.getElementById('front-view-show').innerHTML=div_content; 
}

// Card-preview pop-up box being closed
function closedPopup(){
    document.getElementById("popup-1").classList.toggle("active");
    $('#Front-card').css('display','block');
}

//fetching data from local storage onto the card-face and the text-boxes
function getSavedValue (inputname){
     if (!window.localStorage.getItem(inputname)) {
             return ""; 
           }
      return window.localStorage.getItem(inputname);
 }


//Showing pop-up and saving data 
function popupdata(value){
    if(value != "" && value === "front-view"){
       $('#front-view').css('color','green');
       $('#back-view').css('color','black');
       $('#both-view').css('color','black');
       $('#front-view-show').css('display','block');
       $('#back-view-show').css('display','none');
       $('#both-view-show').css('display','none');
       var div_content=document.getElementById('Front-card-detail').innerHTML;
      document.getElementById('front-view-show').innerHTML=div_content; 
    }else if (value != "" && value === "back-view") {
       $('#front-view').css('color','black');
       $('#back-view').css('color','green');
       $('#both-view').css('color','black');
       $('#front-view-show').css('display','none');
       $('#back-view-show').css('display','block');
       $('#both-view-show').css('display','none');
       var div_content=document.getElementById('Back-card-detail').innerHTML;
      document.getElementById('back-view-show').innerHTML=div_content; 
    }else if (value != "" && value === "both-view") {
       $('#front-view').css('color','black');
       $('#back-view').css('color','black');
       $('#both-view').css('color','green');
       $('#front-view-show').css('display','none');
       $('#back-view-show').css('display','none');
       $('#both-view-show').css('display','block');
       var div_content=document.getElementById('Front-card-detail').innerHTML;
      document.getElementById('front-view-show-card').innerHTML=div_content; 
      var div_content1=document.getElementById('Back-card-detail').innerHTML;
      document.getElementById('back-view-show-card').innerHTML=div_content1; 
    }else{
       $('#front-view').css('color','green');
       $('#back-view').css('color','black');
       $('#both-view').css('color','black');
       $('#front-view-show').css('display','block');
       $('#back-view-show').css('display','none');
       $('#both-view-show').css('display','none');
       var div_content=document.getElementById('Front-card-detail').innerHTML;
      document.getElementById('front-view-show').innerHTML=div_content; 
    }
}

//Making the pop-up box draggable
$(function(){
  $('#popup-1').draggable();
})
   
  $('#accept').click(function() {
    if(this.checked){
     $('.accept').removeAttr("disabled");
    }else{
         $('.accept').attr('disabled', 'disabled');
    }
});


//Redirection to the preview page
  function GoForReview(val){
      var CT_ID = val.value;
      var Front_view = document.getElementById('Front-card-detail').innerHTML;
      var backsidecheck = $('#backsidecheck').val();
      if(backsidecheck==1){
        var Back_view  = document.getElementById('Back-card-detail').innerHTML;
       } 
       if(CT_ID){
        window.localStorage.setItem('card_id',CT_ID);
       }
       if(Front_view.length >20){
        window.localStorage.setItem('front_side',Front_view);
       }  
       if(Back_view.length >20){
        window.localStorage.setItem('back_side',Back_view);
       }
       if(localStorage.getItem('front_side') && localStorage.getItem('card_id')){
          $('#GoForReview').html('Please Wait');
        setTimeout(function(){
           window.location.href=Redirect;
        },2000)
       }  
  }

//Saving the logo/icons placed on the card face
$(function(){
   if($('#edit_page').val()=="1"){
  const mainlogo = window.localStorage.getItem('mainlogoimg');
  const footerlogo = window.localStorage.getItem('footerlogoimg');
 if(mainlogo){
      document.getElementById('mainlogoimg').src=mainlogo;
      $('#mainlogoimg').css('cursor','pointer');
      $('#mainlogoimg').draggable();
    }
 if(footerlogo){
       document.getElementById('footerlogoimg').src=footerlogo;
       $('#footerlogoimg').css('cursor','pointer');
       $('#footerlogoimg').draggable(); 
  }
document.querySelector('.mainlogo').addEventListener('change',function(){
    const mainimg = window.URL.createObjectURL(this.files[0]);
   document.getElementById('mainlogoimg').src=mainimg;
   window.localStorage.setItem('mainlogoimg',mainimg);
});

document.querySelector('.footerlogo').addEventListener('change',function(){
    const footerimg = window.URL.createObjectURL(this.files[0]);
   document.getElementById('footerlogoimg').src= footerimg;
   window.localStorage.setItem('footerlogoimg',footerimg);
});

}

});



 


