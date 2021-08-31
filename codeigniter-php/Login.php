<?php
defined('BASEPATH') OR exit('No direct script access allowed');

// User Login and Logout  
class Login extends CI_Controller {
               
      function __construct() {
             parent::__construct();
             $this->load->model('Common_Model');
             $this->load->library('form_validation');
             $this->load->helper('common_helper');
		     date_default_timezone_set('asia/kolkata');    
      }

// Function For rendering header,footer and dynamic Page content 
    private function render($view="",$data=""){
        $this->load->view('header'); 
          if(!empty($view) && !empty($data)){
            $result['data'] = $data;
            $this->load->view($view,$result);
           }elseif(!empty($view) && empty($data)){
             $this->load->view($view);
           }
           $this->load->view('footer');
     }
 
// Funtion For validating User Login
  public function index(){
       if($this->session->userdata('is_login') == 1 && $this->session->userdata('is_login') && $this->session->userdata('u_type')){
          if($this->session->userdata('u_type') == SUPERADMIN){
              redirect('profile','refresh');
            }else if($this->session->userdata('u_type') == COMPANY){
              redirect('comp_profile','refresh');
            }else if($this->session->userdata('u_type') == EMPLOYEE){
               redirect('emp_profile','refresh'); 
            }  
          }else{
            $result['card_details'] = $this->Common_Model->get_card('tbl_card_category','id','asc',0,6,'status',1);
            $result['page_details'] = $this->Common_Model->get_single_row('tbl_page','status',1,'page_name','home'); 
           if(!empty($result)){
              $this->render("home",$result);  
            }else{
                $this->render("home");
             }         
          }         
      }
      
// Function for validating Super-admin and company Login 
  public function accountLogin(){
       if($this->session->userdata('is_login') == 1 && $this->session->userdata('is_login') && $this->session->userdata('u_type')){
          if($this->session->userdata('u_type') == SUPERADMIN){
              redirect('profile','refresh');
            }else if($this->session->userdata('u_type') == COMPANY){
              redirect('comp_profile','refresh');
            }else if($this->session->userdata('u_type') == EMPLOYEE){
               redirect('emp_profile','refresh'); 
            }  
          }else{ 
                session_destroy();
                session_unset();      
            $this->render("signin");   
           }    
    }
// Function for validating Super-admin and company Login 
  public function login_Check(){
      if($this->session->userdata('is_login') == 1 && $this->session->userdata('is_login') && $this->session->userdata('u_type')){
          if($this->session->userdata('u_type') == SUPERADMIN){
              redirect('profile','refresh');
            }else if($this->session->userdata('u_type') == COMPANY){
              redirect('comp_profile','refresh');
            }else if($this->session->userdata('u_type') == EMPLOYEE){
               redirect('emp_profile','refresh'); 
            }  
         }else{       
            $this->render("signin");   
           }  
     }   

// Function for Register User page 
  public function register(){
           if($this->session->userdata('is_login') == 1 && $this->session->userdata('is_login') && $this->session->userdata('u_type')){
          if($this->session->userdata('u_type') == SUPERADMIN){
              redirect('profile','refresh');
            }else if($this->session->userdata('u_type') == COMPANY){
              redirect('comp_profile','refresh');
            }else if($this->session->userdata('u_type') == EMPLOYEE){
               redirect('emp_profile','refresh'); 
            }  
         }else{    
            $this->render("signup");
           }    
        }

// Function for User Sign in after authentication
  public function signin(){         
        $this->form_validation->set_rules('username', 'Email', 'trim|required|valid_email');
        $this->form_validation->set_rules('password', 'Password', 'trim|required');
        if($this->form_validation->run()){ 
            $username = $this->input->post('username');
            $password = $this->input->post('password');
            $login_type = "";
            $table      = "";
            $id         = "";
            $function   = "";
            $profile    = "";
            if(!empty($this->session->userdata('log_type'))){
                if($this->session->userdata('log_type') == 'superadmin'){
                    $login_type = SUPERADMIN;
                    $table      = "tbl_superadmin";
                    $id         =  "id";
                    $function   =  SUPERADMINFUNCTION;
                    $profile    =  SUPERADMINPROFILE;
                }else if ($this->session->userdata('log_type') == 'company'){
                    $login_type = COMPANY;
                     $table     = "tbl_company";
                     $id        = "comp_id";
                     $function  = COMPANYFUNCTION;
                     $profile   = COMPANYPROFILE;
                }else{
                    $login_type = EMPLOYEE;
                    $table      = "tbl_employee";
                    $id         = "emp_id";
                    $function   = EMPLOYEEFUNCTION;
                    $profile    = EMPLOYEEPROFILE;
                }
              }else{
                 $login_type = EMPLOYEE;
                 $table      = "tbl_employee";
                 $id         = "emp_id";
                 $function   = EMPLOYEEFUNCTION;
                 $profile    = EMPLOYEEPROFILE;
              } 
         $UserEmployeeExists= $this->Common_Model->get_single_row('tbl_login','username',$username,'password',md5($password),'loginType_id',$login_type);
         if(!empty($UserEmployeeExists)){
            $UserEmployeeLoginStatus= $this->Common_Model->checkstatus('tbl_login','emp_id',$UserEmployeeExists->emp_id,'status',1);
            $UserEmployeeStatus= $this->Common_Model->checkstatus($table,$id,$UserEmployeeExists->emp_id,'status',1);
            $loginupdate = array(
                'login_exists' => 1,
                'last_login'   => date("Y-m-d h:i:sa"),
            );
             $updateresult  = $this->Common_Model->update_data('tbl_login',$loginupdate,'emp_id',$UserEmployeeExists->emp_id); 
             if(!empty($UserEmployeeStatus) && !empty($UserEmployeeLoginStatus)){
                $session_data = array(
                   'id'     => $UserEmployeeExists->emp_id,
                   'u_type' =>  $login_type,
                   'is_login' => 1,
                  );
             $this->session->set_userdata($session_data);
               $array = array(
                 'error'             =>  false,
                 'functionnm'          =>  $function,
                 'message'           =>  "Account Active!$profile",
                 'error_type'        =>   1,
                 'button'             =>  "Sign In",
               );
            }else{
                $array = array(
                'error'              =>  true,
                'button'             =>  "Sign In",
                'message'            =>  "User Not Active!Please Contact To Administrator",
                'error_type'         =>  3,
           );
            }
         }else{
              $array = array(
              'error'              =>  true,
              'button'             =>  "Sign In",
              'message'            =>  "Invalid User",
              'error_type'         =>  2,
           );
         }
        }else{
            $array = array(
            'error'              => true,
            'button'             =>  "Sign In",
            'message'            =>  "",
            'username_error'     => form_error('username'),
            'password_error'     => form_error('password'),
           );
        }
        echo json_encode($array);
     }

// Functio for saving registered user data in database 
  public function signup(){
        $this->form_validation->set_rules('emp_name', 'Name', 'trim|required');
        $this->form_validation->set_rules('emp_password', 'Password', 'trim|required|max_length[20]|min_length[8]');
        $this->form_validation->set_rules('confirm_password', 'Confirm Password', 'trim|required|matches[emp_password]|max_length[20]|min_length[8]');
        $this->form_validation->set_rules('emp_email', 'Email', 'trim|required|valid_email');
        $this->form_validation->set_rules('type', 'Type', 'trim|required');
        if($this->form_validation->run()){ 
          $emp_name     = $this->input->post('emp_name');
          $emp_password = $this->input->post('emp_password');
          $con_password = $this->input->post('confirm_password');
          $emp_email    = $this->input->post('emp_email');
           if($this->input->post('type') == "User"){
          $formdata = array(
                 'emp_name'     => $emp_name,
                 'emp_email'    => $emp_email,
                 'status'       => 2,
                 'comp_id'      => 0,
                 'created_date' => date("Y-m-d h:i:sa"),
                 'updated_date' => date("Y-m-d h:i:sa"),
            );
          $Insert = $this->Common_Model->add_data('tbl_employee',$formdata);
          $login_type = EMPLOYEE;
           }else{
            $Cformdata = array(
                 'comp_name'     => $emp_name,
                 'comp_email '    => $emp_email,
                 'status'       => 2,
                 'created_by'   => $emp_name,
                 'updated_by'   => $emp_name,
                 'created_date' => date("Y-m-d h:i:sa"),
                 'updated_date' => date("Y-m-d h:i:sa"),
            );
          $Insert = $this->Common_Model->add_data('tbl_company',$Cformdata);
          $login_type = COMPANY;
           }
          if(!empty($Insert)){
             $logindata = array(
                'emp_id'        => $Insert,
                'username'      => $emp_email,
                'password'      => md5($con_password),
                'created_date'  => date("Y-m-d h:i:sa"),
                'updated_date'  => date("Y-m-d h:i:sa"),
                'status'        => 2,
                'last_login'    => Null,
                'login_exists'  => 2,
                'loginType_id'  => $login_type,
            );
          $LoginInsert = $this->Common_Model->add_data('tbl_login',$logindata);
          $tokengenerate = md5($emp_name).rand(1000,5000);
           $logindata = array(
                'emp_id'        => $Insert,
                'gen_tokan'     => $tokengenerate,
                'created_date'  => date("Y-m-d h:i:sa"),
                'updated_date'  => date("Y-m-d h:i:sa"),
                'status'        => 2,
                'loginType_id'  => $login_type,
            );
          $LoginInsert = $this->Common_Model->add_data('tbl_token',$logindata);
          } else{
             $array = array(
            'error'              => true,
            'button'             =>  "Sign In",
            'message'            =>  "<div class='alert alert-danger' style='width:max-content'>Somthing Wrong!Please try After Some Time</div>",
           );
          } 
          if(!empty($Insert) && !empty($LoginInsert)){
            $array = array(
            'error'              => false,
            'button'             =>  "Sign In",
            'message'            =>  '<div class="alert alert-success" style="width:max-content">Your Inforamtion Successfully Saved With Us!Please Login With Email and Password</div>',
           );
          }else{
             $array = array(
            'error'              => true,
            'button'             =>  "Sign In",
            'message'            => '<div class="alert alert-danger" style="width:max-content">Somthing Wrong!Please try After Some Time</div>',
           );
          }
        }else{
            $array = array(
            'error'              => true,
            'button'             =>  "Sign In",
            'message'            =>  "",
            'name_error'         => form_error('emp_name'),
            'password_error'     => form_error('emp_password'),
            'con_pass_error'     => form_error('confirm_password'),
            'email_error'        => form_error('emp_email'),
            'type_error'         => form_error('type'),
            );
        }
        echo json_encode($array);
     }

// Function for validating emailID at the time of registeration 
  public function check_email(){
        if($this->input->post()){
            if($this->input->post('type') == "Company"){
                $result = $this->Common_Model->get_single_row('tbl_company','comp_email',$this->input->post('email')); 
            }else{
             $result = $this->Common_Model->get_single_row('tbl_employee','emp_email',$this->input->post('email')); 
            } 
             if(!empty($result)){
                echo "Please Enter Other Email Address"; 
                die;  
              }
        } 
     }

// Function for sending email for 'email verification' to registered user 
  public function sendmail(){  
        $name  = $this->input->post('name');
        $email = $this->input->post('email');
        $type  = $this->input->post('type');
        $use   = $type == "User" ? "Individual User" : "Company";
        $stringCode = $this->randomString(8);
        // Subject
        $subject = 'Registration Mail-Virtual Cards';
        // Message 
        $message = "";
        $message = '<div style="font-family: Helvetica,Arial,sans-serif;min-width:1000px;overflow:auto;line-height:2">
       <div style="margin:50px auto;width:70%;padding:20px 0">
        <div style="border-bottom:1px solid #eee">
         <a href="" style="font-size:1.4em;color: #00466a;text-decoration:none;font-weight:600">VIRTUAL CARDS</a></div>
        <p style="font-size:1.1em">Hi '.$name.',</p>
        <p>Thank you for register as a '.$use. ' in  Virtual cards platform. Use the following OTP to complete your Sign Up procedures.</p>
        <h2 style="background: #00466a;margin: 0 auto;width: max-content;padding: 0 10px;color: #fff;border-radius: 4px;">'.$stringCode.'</h2>
       <p style="font-size:0.9em;">Regards,<br />Virtual Cards</p>
       <hr style="border:none;border-top:1px solid #eee" />
       <div style="float:right;padding:8px 0;color:#aaa;font-size:0.8em;line-height:1;font-weight:300">
        <p>Zapbuild Technology Pvt Ltd.</p></div></div></div>';

    
  $headers[] = "MIME-Version: 1.0";
  $headers[] = "Content-type: text/html; charset=iso-8859-1";
  $headers[] = "X-Priority: 3";
  $headers[] = "X-Mailer: PHP". phpversion();
  $headers[] = "Reply-To: Zapbuild <connect@zapbuild.com>";
  $headers[] = "Return-Path:Zapbuild <ankureshverma@zapbuild.com>";
  $headers[] = "From:Zapbuild <oliviazoey01@gmail.com>";
        
    if(mail($email,$subject,$message,implode("\r\n", $headers))) {
         $tempdata =array(
                  'otp' =>  $stringCode, 
                  'name'=>  $name,
                  'type'=>  $type,
                  'email'=> $email,
          );
         $LoginInsert = $this->Common_Model->add_data('tbl_emailotp',$tempdata);
        $array = array(
            'error'   => false,
            'message' =>  '<div class="alert alert-success"><strong>The OTP is sent on your email address. Please Check Your Email.</div>',
           );
       }else{
       $array = array(
            'error'   => true,
            'massage' =>'<div class="alert alert-danger"><strong>Failed Send Otp.</strong></div>',
            );
       }
       echo json_encode($array);
     }
    
 // Function to generate randomString for email verification code    
    private function randomString($stringlng){
        $chary = array("a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z","0", "1", "2", "3", "4", "5", "6", "7", "8", "9","A", "B", "C", "D", "E", "F", "G",
            "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", 
            "S", "T", "U", "V", "W", "X", "Y", "Z");
        $return_str = "";
        for ($x=0; $x<=$stringlng; $x++) {
        $return_str .= $chary[rand(0, count($chary)-1)];
             }
        return $return_str;
    }

  // Function to validate the code entered by the user    
   public function verifyMail(){
        $name  = $this->input->post('name');
        $email = $this->input->post('email');
        $type  = $this->input->post('type');
        $EmailOtp   = $this->input->post('Emailotp');
        $result = $this->Common_Model->get_single_row('tbl_emailotp','otp',$EmailOtp,'email',$email,'name',$name,'status',2);
        if(!empty($result->otp) && ($result->otp === $this->input->post('Emailotp'))){
        if(!empty($result)){ 
          $update = array(
            'status' => 1,
          );
          $upresult = $this->Common_Model->update_data('tbl_emailotp',$update,'id',$result->id);
          if($upresult){
            $response=array(
            'error' => false,
            'msg'   => '<div class="alert alert-info">
            The OTP Verification Successfully!.</div>',
         );  
          }
         else{
          $response=array(
            'error' => true,
            'msg'   => '<div class="alert alert-warning">The OTP Verification Failed!Please Try Again.</div>',
          );
          }
         }
     }
    else{
          $response=array(
            'error' => true,
            'msg'   => '<div class="alert alert-warning">The OTP Verification Failed!Please Try Again.</div>',
          );
        }
    echo json_encode($response);
 }

// Fuction to show data of About Us page 
 public function about(){
    $result['card_details'] = $this->Common_Model->get_card('tbl_card_category','id','asc',0,6,'status',1);
    $result['page_details'] = $this->Common_Model->get_single_row('tbl_page','status',1,'page_name','about');
      if(!empty($result)){
           $this->render('about',$result);
      } else {
        $this->render('about'); 
      }
        
    }

// Function to save details entered on Contact Us page
 public function saveContact(){
       $this->load->library('form_validation');
       $this->form_validation->set_rules('name', 'Name', 'trim|required|max_length[100]'); 
       $this->form_validation->set_rules('email', 'Email', 'trim|required|valid_email|is_unique[tbl_contact.email]');
        $this->form_validation->set_rules('subject', 'Subject', 'trim|required');
       if($this->form_validation->run()){
          $name    = $this->input->post('name');
          $email   = $this->input->post('email');
          $subject = $this->input->post('subject');
          $msg     = $this->input->post('message');
        $formdata = array(
           'name'      => $name,
           'email'     => $email,
           'msg'       => $msg,
           'created_date' => date("Y-m-d h:i:sa"),
           'updated_date' => date("Y-m-d h:i:sa"),
           'subject'     => $subject,
          );
      $resultdata = $this->Common_Model->add_data('tbl_contact',
        $formdata);
        if($resultdata){
            $array = array(
                'error'   => false,
                'message' =>  '<div class="alert alert-success">Thanks For Register With Us! We will contact as soon as possible</div>',
                'refresh' =>  '',
                 );
          } else{
            $array = array(
              'error'   => true,
              'message' =>  '<div class="alert alert-danger">Somthing Went Wrong! please try After Some time.</div>',
             );
          }
        } else{
            $array = array(
              'error'           => true,
              'button'          => "Submit",
              'name_error'      => form_error('name'),
              'email_error'     => form_error('email'),
              'sub_error'       => form_error('subject'), 
               );
          }
    echo json_encode($array); 
    }

 // Function for showing Contact Us page 
 public function contact(){
    $result['page_details'] = $this->Common_Model->get_single_row('tbl_page','status',1,'page_name','contact');
    if(!empty($result)){
           $this->render('contact',$result);
      } else {
         $this->render('contact'); 
      }
  }

// Function for showing Sub-category card list according to card ID
  public function subcard(){
    if(!empty($_GET)){
     $id = decrypt_url($_GET['detail']);
     if(!empty($id)){
         $checkurl = substr($_GET['detail'],-2);
      if($checkurl=="09"){
        $page ="";
        $result['subcard_details'] = $this->Common_Model->get_data('tbl_card_subcategory','id','asc','cat_id',$id,'status',1);
        $result['card_details'] = $this->Common_Model->get_single_row('tbl_card_category','id',$id,'status',1);
          if(!empty($result['subcard_details'])){
               $page = 'subcate';
          }else{
              $page = 'template';
          }
          $this->render($page,$result);
        }else{
        redirect('Login','refresh'); 
      }
     }else{
        redirect('Login/pageNotFound','refresh'); 
     }
     }else{
      redirect('Login/pageNotFound','refresh');
    }
  }

// Function for listing templates
  public function template(){
    if(!empty($_GET)){
     $id = decrypt_url($_GET['detail']);
     if(!empty($id)){
         $checkurl = substr($_GET['detail'],-2);
      if($checkurl=="09"){
        $result['layouts'] = $this->Common_Model->get_data('tbl_layout','id','asc','subcate_id',$id,'status',1);
        $result['subcate_id'] = $id;
         if(!empty($result['layouts'])){
               $this->render('template',$result);     
        }else{
        redirect('Login/pageNotFound','refresh'); 
      }
     }else{
        redirect('Login/pageNotFound','refresh'); 
     }
     }else{
      redirect('Login/pageNotFound','refresh');
    }
  }
}

// Function to show template details
public function template_detail(){
    if(!empty($_GET)){
     $id = decrypt_url($_GET['detail']);
     if(!empty($id)){
         $checkurl = substr($_GET['detail'],-2);
      if($checkurl=="09"){
        $result['templates_details'] = $this->Common_Model->get_data('tbl_layout','id','asc','temp_id',$id,'status',1);
         if(!empty($result)){
               $this->render('template_detail',$result);     
        }else{
        redirect('Login/pageNotFound','refresh'); 
      }
     }else{
        redirect('Login/pageNotFound','refresh'); 
     }
     }else{
      redirect('Login/pageNotFound','refresh');
    }
  }
}

// Function to show Edit Template page 
public function edit_template(){
    if(!empty($_GET)){
     $id = decrypt_url($_GET['layout']);
     if(!empty($id)){
         $checkurl = substr($_GET['layout'],-2);
      if($checkurl=="09"){
        $result= $this->Common_Model->get_single_row('tbl_layout','id',$id,'status',1);
         if(!empty($result)){
               $this->render('edit_template',$result);     
        }else{
        redirect('Login/pageNotFound','refresh'); 
      }
     }else{
        redirect('Login/pageNotFound','refresh'); 
     }
     }else{
      redirect('Login/pageNotFound','refresh');
    }
  }
}

  // Function to show Thank You page post Contact Us page
  public function thankyou(){
       $this->render('thankyou');
    }
     
  // Showing page to save details in cookies after Preview and Edit     
  public function SaveCardInformation(){
          $card_id = decrypt_url($this->input->post('CT_ID'));
          $front_view = trim($this->input->post('Front_view'));
          $frontview = !empty($front_view) ? $front_view : " ";      
          $back_view = trim($this->input->post('Back_view'));
          $backview = !empty($back_view) ? $back_view : " ";      
          if(!empty($card_id)){
             setcookie('front_side',$frontview,time()+(60*60*24*2));
             setcookie('back_side',$backview,time()+(60*60*24*2));
             setcookie('card_id',$card_id,time()+(60*60*24*2));
           if(!empty($_COOKIE)){
             $array = array(
                 'error' => false,
                 'card_id'  => encrypt_url($card_id)
                );
            echo json_encode($array);
             die; 
            }    
      }
  }

  // Redirecting to Confirmation page post saving card details
  public function ConfirmationCard(){
         if(!empty($_GET['card']) && !empty($_GET)){
            if(!empty($_COOKIE['card_id'])){
                $response['card_id'] =  $_COOKIE['card_id'];
                if(!empty($_COOKIE['front_side'])){
                   $response['front_side'] = $_COOKIE['front_side']; 
                }      
              if(!empty($_COOKIE['back_side'])) {
                $response['back_side'] = $_COOKIE['back_side'];
               }
               $this->render('confirmation',$response); 
            }else{
                $this->render('confirmation');
            }     
        }
   }
 
 // Function to show all cards on click
  public function AllCard(){
        $result['card_details'] = $this->Common_Model->get_data('tbl_card_category','id','asc','status',1);
        $result['page_details'] = $this->Common_Model->get_single_row('tbl_page','status',1,'page_name','card');
        if(!empty($result['card_details']) || !empty($result['card_details'])){
           $this->render('allcard',$result);  
        }else{
            redirect('Login/pageNotFound','refresh'); 
        }
       
     }

// Redirecting to Page Not Found 
  public function pageNotFound(){
           $this->load->view('frontend/header');
           $this->load->view('pagenotfound');
           $this->load->view('frontend/footer');
     }

// User logout
  public function logout(){
        if($this->session->userdata('is_login') || $this->session->userdata('log_type')){
             session_unset();
             session_destroy();
            redirect('Login','refresh');
         }else{
            redirect('Login','refresh');
         }
     }


}