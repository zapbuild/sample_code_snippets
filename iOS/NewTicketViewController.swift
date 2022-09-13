import UIKit
/**
 NewTicketViewController.swift
 Team Square
 
 - Author:
 Poonam Chandel
 
 - Copyright:
 Zapbuild Technologies Pvt Ltd
 
 - Date:
 29/07/22
 
 - Version:
 1.0
 */

class NewTicketViewController: BaseViewController {
    //MARK: -  Outlets and Variables 
    @IBOutlet weak var navigationBarView: CustomNavigationBar!
    @IBOutlet weak var todayButton: UIButton!
    @IBOutlet weak var within5DaysButton: UIButton!
    @IBOutlet weak var within2DaysButton: UIButton!
    @IBOutlet weak var notUrgentButton: UIButton!
    @IBOutlet weak var detailTextView: UITextView!
    @IBOutlet weak var attachmentImageView: UIImageView!
    
    private var profileImagePicker : ProfileImagePicker?
    private var imagePicker : UIImagePickerController?
    private var urgencyLevel: Int? = 1
    private var loggedInUser: User?
   
    //MARK: -  View Controller Life Cycle Methods 
    override func viewDidLoad() {
        super.viewDidLoad()
        configure()
    }
    
    //MARK: -  Button Actions 
    @IBAction func uploadButtonTapped(_ sender: UIButton) {
        DispatchQueue.main.async {
            self.profileImagePicker!.imageDelegate = self
            self.profileImagePicker!.presentImagePickerSourceActionSheet(controller: self, iPadActionsourceView: self.view)
        }
    }
    @IBAction func submitButtonTapped(_ sender: UIButton) {
        if InputValidations.checkAddNewTicketValidation(text: detailTextView.text ?? "", viewController: self){
            addNewTicket()
        }
    }
    @IBAction func urgencyLevelButtonTapped(_ sender: UIButton) {
        switch sender.tag{
        case 0:
            todayButton.isSelected = true
            within2DaysButton.isSelected = false
            within5DaysButton.isSelected = false
            notUrgentButton.isSelected = false
            urgencyLevel = 1
        case 1:
            todayButton.isSelected = false
            within2DaysButton.isSelected = true
            within5DaysButton.isSelected = false
            notUrgentButton.isSelected = false
            urgencyLevel = 2
        case 2:
            todayButton.isSelected  = false
            within2DaysButton.isSelected = false
            within5DaysButton.isSelected = true
            notUrgentButton.isSelected = false
            urgencyLevel = 3
        case 3:
            todayButton.isSelected  = false
            within2DaysButton.isSelected = false
            within5DaysButton.isSelected = false
            notUrgentButton.isSelected = true
            urgencyLevel = 4
        default:
            break
        }
    }
    //MARK: -  UI update method  
    private func configure(){
        navigationBarView.navigationTitleLabel.text = "New Ticket"
        navigationBarView.sideMenuIconImageView.image = UIImage(named: "Back White")!
        navigationBarView.sideMenuButtonPressed = {
            self.popToPreviousScreen(self)
        }
        profileImagePicker = ProfileImagePicker()
        imagePicker = UIImagePickerController()
        loggedInUser = UserDefaultHandler.shared.user
        self.detailTextView.placeholder = "Add details here.."
        self.detailTextView.textContainerInset = UIEdgeInsets(top: 20, left: 12, bottom: 20, right: 12)
       
    }
    //MARK: -  User Phone Number Api  
    private func getUserPhoneNumber(){
        CommonUtilities.showHUD()
        UserPhoneNumberNetworkService.callApi(id: loggedInUser?.userId ?? 0 ) { (result: Result<LoginResponseData,Error>) in
            DispatchQueue.main.async {
                CommonUtilities.hideHUD()
                switch result{
                case .success(let responseData):
                    if responseData.apiCode == ApiCode.success.rawValue{
                    }else{
                        self.alertWith(title: Constants.AlertTitles.alert, message: responseData.message ?? "")
                    }
                    
                case .failure(let error):
                    self.alertWith(title: "", message: error.localizedDescription)
                }
            }
            
        }
    }
    //MARK: -  Get Urgency Level Api 
    private func getUrgencyLevel(){
        CommonUtilities.showHUD()
        UrgencyLevelNetworkService.callApi() { (result: Result<UrgencyLevelResponse,Error>) in
            DispatchQueue.main.async {
                CommonUtilities.hideHUD()
                switch result{
                case .success(let responseData):
                    print(responseData)
                    
                case .failure(let error):
                    self.alertWith(title: "", message: error.localizedDescription)
                }
            }
            
        }
    }

    //MARK: -  Add New Ticket Api 
    private func addNewTicket(){
        let fullName = "\(loggedInUser?.firstName ?? "") \(loggedInUser?.lastName ?? "")"
        let parameters :[String: Any] = [
            "email" : loggedInUser?.email ?? "",
            "name"  : fullName,
            "urgency_level" : urgencyLevel ?? 0,
            "detail" : detailTextView.text ?? ""
        ]
        CommonUtilities.showHUD()
        AddNewTicketNetworkService.callApi(image: attachmentImageView.image ?? UIImage(named: ""), parameters: parameters){ (result: Result<TicketsResponseData,Error>) in
            DispatchQueue.main.async {
                
                CommonUtilities.hideHUD()
    
                switch result{
                case .success(let responseData):
                    if responseData.apiCode == ApiCode.addSuccess.rawValue{
                        self.alertWith(title: Constants.AlertTitles.success, message: Constants.AlertMessages.addNewTicketSuccess) {
                            self.popToPreviousScreen(self)
                        }
                    }else{
                        self.alertWith(title: "", message: responseData.message ?? "")
                    }
                case .failure(let error):
                    self.alertWith(title: "", message: error.localizedDescription)
                }
            }
        }
    }
    
}
//MARK: -  Extensions 
extension NewTicketViewController: ProfileImagePickerDelegate{
    func imageSelectionSuccessful(selectedImage: UIImage) {
        attachmentImageView.image = selectedImage
    }
    
    func imageSelectionCancelled() {
       
    }
}

extension NewTicketViewController: UITextViewDelegate{
    func textView(_ textView: UITextView, shouldChangeTextIn range: NSRange, replacementText text: String) -> Bool {
        
        let maxLength = textView.text!.count + text.count - range.length
        if (textView == detailTextView){
            return maxLength <= Constants.InputLengthConstraints.Maximum.description
        }else{
            return true
        }
    }
}
