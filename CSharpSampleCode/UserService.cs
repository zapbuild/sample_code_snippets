using BarrelApp.Data;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;
using System.Web.UI.HtmlControls;
namespace BarrelApp.App_Code.Service
{
    //
    // Summary:
    //     User service class handle to communicate with logged in user details.
    public class UserService
    {
        //
        // Summary:
        //      Member variable for class instance
        private static UserService _instance;
        //
        // Summary:
        //      Member variable for current loggedIn use object
        private AspNetUser currentUser = null;
        //
        // Summary:
        //      get and set the instance of UserService class
        // Return:
        //      Instance of UserService class
        public static UserService Instance
        {
            get
            {
                if (_instance == null)
                {
                    _instance = new UserService();
                }
                return _instance;
            }
        }
        //
        // Summary:
        //      get and set the loggedIn user object
        // Return:
        //      Instance of AspNetUser
        public AspNetUser LogInUser()
        {
            if (currentUser == null)
            {
                using (BarrelDBEntities barEnt = new BarrelDBEntities())
                {
                    currentUser = barEnt.AspNetUsers.FirstOrDefault(rec => rec.Email == HttpContext.Current.User.Identity.Name);
                }
            }
            return currentUser;
        }
        //
        // Summary:
        //      set the loggedIn user object null
        //      being use during logout
        public void ResetLogInUser()
        {
            currentUser = null;
        }
        //
        // Summary:
        //      set the loggedIn user object updated data
        //      being use during loggedIn user update profile
        public void SetLogInUser(AspNetUser user)
        {
            currentUser = user;
        }
        //
        // Summary:
        //      get the loggedIn user is admin
        // Return:
        //       true/false
        public bool IsAdmin()
        {
            AspNetUser user = LogInUser();
            return (user.PID == "1");
        }
        //
        // Summary:
        //      get the loggedIn user is internal user
        // Return:
        //       true/false
        public bool IsInternalUser()
        {
            AspNetUser user = LogInUser();
            return (user.PID == "2");
        }
        //
        // Summary:
        //      get the loggedIn user is external user
        // Return:
        //       true/false
        public bool IsExternalUser()
        {
            AspNetUser user = LogInUser();
            return (user.PID == "3");
        }
        //
        // Summary:
        //      get the loggedIn user is client user
        // Return:
        //       true/false
        public bool IsClientUser()
        {
            AspNetUser user = LogInUser();
            return (user.PID == "4");
        }
        //
        // Summary:
        //      get the loggedIn user Id
        // Return:
        //       loggedIn user Id
        public int UserID()
        {
            AspNetUser user = LogInUser();
            return user.UserID;
        }
        //
        // Summary:
        //      get the loggedIn user email password that being used when user send mail
        //      using by his/her account
        // Return:
        //       loggedIn Email passowrd
        public string UserSendEmailMailAddress()
        {
            AspNetUser user = LogInUser();
            return user.Email;
        }
        //
        // Summary:
        //      get the loggedIn user email from name that being used when user send mail
        //      using by his/her account
        // Return:
        //       loggedIn from name
        public string UserSendEmailMailFromName()
        {
            AspNetUser user = LogInUser();
            return string.Format("{0} {1}", user.FirstName, user.LastName);
        }
    }
}