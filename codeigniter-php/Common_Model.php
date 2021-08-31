<?php
defined('BASEPATH') OR exit('No direct script access allowed');

// Model For Common Facility 
class Common_Model extends CI_Model {

// Function used for saving data in table by passing Table name and data of array..
    public function add_data($table,$data){
        if(!empty($table) && !empty($data)){
              $query = $this->db->insert($table,$data);
              if($query){
                 return $this->db->insert_id();;
              }else{
                  return false;
              }
        }else{
            return false;
        }
    }

// Function used to get resultant Data  by passing Table Name and Where Conditions
    public function get_data($table,$id="",$order_by="",$col1="",$val1="",$col2="",$val2="",$col3="",$val3=""){
        if(!empty($table)){
            if(!empty($id) && !empty($order_by)){
               $this->db->order_by($id,$order_by); 
            }     
            if(!empty($col1)){
                $this->db->where($col1,$val1);
            }
            if(!empty($col2) && !empty($val1)){
                $this->db->where($col2,$val2);
            }
            if(!empty($col3 && !empty($val3))){
                $this->db->where($col3,$val3);
            }
            $query = $this->db->get($table);
            if($query->num_rows()>0){
                return $query->result();
            } else{
                return false;
            }
         } 
        }
    
// Function used to get single row of data by passing Table Name and Where Condition 
  public function get_single_row($table,$column1="",$value1="",$column2="",$value2="",$column3="",$value3=""){
        if(!empty($table)){
             if(!empty($column1) && !empty($value1)){
                $this->db->where($column1,$value1);
             }
            if(!empty($column2) && !empty($value2)){
                $this->db->where($column2,$value2);
            }
             if(!empty($column3) && !empty($value3)){
                $this->db->where($column3,$value3);
            }
            $query = $this->db->get($table);
            if($query->num_rows()>0){
                return $query->row();
            } else{
                return false;
            }
        }
}

// Function used for updating data in table by passing Table Name and data of array..
public function update_data($table,$data,$column1="",$value1="",$column2="",$value2="",$column3="",$value3=""){
    if(!empty($table)){
        if(!empty($column1) && !empty($value1)){
            $this->db->where($column1,$value1);
        }
        if(!empty($column2) && !empty($value2)){
            $this->db->where($column2,$value2);
        }
         if(!empty($column3) && !empty($value3)){
            $this->db->where($column3,$value3);
        }
        $query = $this->db->update($table,$data);
        if($query){
            return $query;
        } else{
            return false;
        }
    }
}
// Function used for deleting data in table by passing Table Name and Where Condition
public function delete_row($table,$column1="",$value1="",$column2="",$value2=""){
    if(!empty($table)){
        if(!empty($column1) && !empty($value1)){
            $this->db->where($column1,$value1);
        }
         if(!empty($column2) && !empty($value2)){
            $this->db->where($column2,$value2);
        }
        $query = $this->db->delete($table);
        if($query){
            return $query;
        } else{
            return false;
        }
        }
    }

 // Function used to check status in table by passing Table Name and Condition
    public function checkstatus($table,$column1="",$value1="",$status="",$value=""){
        if(!empty($table)){
            if(!empty($column1) && !empty($value1)){
                $this->db->where($column1,$value1);
            }
             if(!empty($status) && !empty($value)){
                $this->db->where($status,$value);
            }
            $query = $this->db->get($table);
            if($query->num_rows() > 0){
                return true;
            } else{
                return false;
            }
        }
      }

// Function used to set limit on fetched number of cards by passing Table Name and Limit Condition
 public function get_card($table,$orderby,$orderval,$limitstart="",
        $limitend="",$col1="",$val1="",$col2="",$val2=""){
          if(!empty($table)){
                $this->db->order_by($orderby,$orderval);
                if(!empty($limitend)){
                     $this->db->limit($limitend,$limitstart);
                }
                if(!empty($col1)){
                    $this->db->where($col1,$val1);
                }
                if(!empty($col2) && !empty($val2)){
                    $this->db->where($col2,$val2);
                }
                $query = $this->db->get($table);
                if($query->num_rows()>0){
                    return $query->result();
                } else{
                    return false;
                }
            }
       }

// Function used to get sum of all the columns by Passing Table Name and Where Condition
    public function get_total_data($table,$sumcol,$group_by,$col1="",$val1="",$col2="",$val2="",$col3="",$val3=""){
         if(!empty($table)){
            if(!empty($sumcol)){
               $this->db->select_sum($sumcol);  
            }
           if(!empty($col1) && !empty($val1)){
                $this->db->where($col1,$val1);
             }
          if(!empty($col2) && !empty($val2)){
                $this->db->where($col2,$val2);
            }
             if(!empty($col2) && !empty($val2)){
                $this->db->where($col2,$val2);
            }if(!empty($group_by)){
                 $this->db->group_by($group_by);
            }  
            $query = $this->db->get($table);
           if($query->num_rows()>0){
                    return $query->row();
             } else{
                    return false;
               }
            }
       }
}



