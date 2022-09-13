import UIKit
import HCSStarRatingView
/**
 TicketRatingViewController.swift
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
class TicketRatingViewController: UIViewController {
    
    //MARK: @IBOutlets
    @IBOutlet weak var ticketIDLabel: UILabel!
    @IBOutlet weak var ticketDescriptionLabel: UILabel!
    @IBOutlet weak var starRatingView: HCSStarRatingView!
    @IBOutlet weak var ratingCommentsTextView: UITextView!
    @IBOutlet weak var sendRatingButton: UIButton!
    
    //MARK: Variables
    public var ticketResults: TicketResults?
    
    //MARK: View Life Cycle
    override func viewDidLoad() {
        super.viewDidLoad()
        configure()
    }
    
    //MARK: @IBActions
    @IBAction func closeButtonTapped(_ sender: UIButton) {
        self.dismiss(animated: true)
    }
    
    @IBAction func sendRatingButtonTapped(_ sender: UIButton) {
        updateTicketRating()
    }
    
    //MARK: Private functions
    private func configure(){
        getTicketDetails()
    }
    
    private func getTicketDetails(){
        CommonUtilities.showHUD()
        TicketDetailsNetworkService.callApi(id: ticketResults?.id ?? 0) { (result: Result<TicketDetailsResponseData,Error>) in
            DispatchQueue.main.async {
                CommonUtilities.hideHUD()
                switch result{
                case .success(let responseData):
                    if responseData.apiCode == ApiCode.success.rawValue, let ticketData = responseData.tickets{
                        self.ticketResults = ticketData
                        self.sendRatingButton.setTitle((self.ticketResults?.ticketRating?.rating ?? "").isEmpty ? "Send Rating" : "Update Rating" , for: .normal)
                        self.ticketIDLabel.text = " Ticket ID : \(self.ticketResults?.id ?? -1)"
                        self.ticketDescriptionLabel.text = self.ticketResults?.detail
                        let ratingValue = Double(self.ticketResults?.ticketRating?.rating ?? "")
                        self.starRatingView.value = ratingValue ?? 0
                        self.ratingCommentsTextView.text = self.ticketResults?.ticketRating?.comments
                    }else{
                        AlertUtility.showAlert(self, title: Constants.AlertTitles.alert, message: responseData.message ?? "")
                    }
                    
                case .failure(let error):
                    AlertUtility.showAlert(self,title: "", message: error.localizedDescription)
                }
            }
            
        }
    }
    
    private func updateTicketRating(){
        let parameters : [String: Any] = [
            "id" : ticketResults?.id ?? 0,
            "rating" : (starRatingView.value),
            "comment" : ratingCommentsTextView.text ?? ""
        ]
        CommonUtilities.showHUD()
        TicketRatingNetworkService.callApi(id: ticketResults?.id ?? 0, parameters: parameters) { (result: Result<TicketDetailsResponseData,Error>) in
            DispatchQueue.main.async {
                CommonUtilities.hideHUD()
                switch result{
                case .success(let responseData):
                    if responseData.apiCode == ApiCode.success.rawValue{
                        AlertUtility.showAlert(self, title: Constants.AlertTitles.success, message: Constants.AlertMessages.ticketUpdateSuccess, cancelButton: "OK") { _, _ in
                            self.dismiss(animated: true)
                        }
                    }else{
                        AlertUtility.showAlert(self, title: Constants.AlertTitles.alert, message: responseData.message ?? "")
                    }
                    
                case .failure(let error):
                    AlertUtility.showAlert(self,title: "", message: error.localizedDescription)
                }
            }
            
        }
    }
}
