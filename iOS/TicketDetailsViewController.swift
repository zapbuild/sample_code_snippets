import UIKit
/**
 TicketDetailsViewController.swift
 Team Square
 
 - Author:
 Poonam Chandel
 
 - Copyright:
 Zapbuild Technologies Pvt Ltd
 
 - Date:
 26/07/22
 
 - Version:
 1.0
 */
class TicketDetailsViewController: BaseViewController {
    
    //MARK: -  Outlets and Variables 
    @IBOutlet weak var ticketIDLabel: UILabel!
    @IBOutlet weak var createdByLabel: UILabel!
    @IBOutlet weak var emailLabel: UILabel!
    @IBOutlet weak var phoneLabel: UILabel!
    @IBOutlet weak var urgencyLevelLabel: UILabel!
    @IBOutlet weak var departmentLabel: UILabel!
    @IBOutlet weak var detailLabel: UILabel!
    @IBOutlet weak var statusLabel: UILabel!
    @IBOutlet weak var toBeAcceptedLabel: UILabel!
    @IBOutlet weak var assignedLabel: UILabel!
    @IBOutlet weak var showRatingLabel: UILabel!
    @IBOutlet weak var commentsContainerView: UIView!
    @IBOutlet weak var commentsTableView: UITableView!
    @IBOutlet weak var commentTableViewHeightConstraint: NSLayoutConstraint!
    @IBOutlet weak var logContainerView: UIView!
    @IBOutlet weak var logsTableView: UITableView!
    @IBOutlet weak var logTableViewHeightConstraint: NSLayoutConstraint!
    @IBOutlet weak var navigationBarView: CustomNavigationBar!
    
    public var ticket: TicketResults?
    private var logs: [Logs]? = []
    private var comments: [Comments]? = []
    
    //MARK: -  View Controller Life Cycle Methods 
    override func viewDidLoad() {
        super.viewDidLoad()
        configure()
        getTicketLogDetails()
        
    }
    //MARK: -  Methods 
    private func configure(){
        navigationBarView.navigationTitleLabel.text = "Ticket Details"
        navigationBarView.sideMenuIconImageView.image = UIImage(named: "Back White")!
        navigationBarView.sideMenuButtonPressed = {
            self.popToPreviousScreen(self)
        }
        commentsTableView.estimatedRowHeight = 98.0
        commentsTableView.rowHeight = UITableView.automaticDimension
        logsTableView.estimatedRowHeight = 143.0
        logsTableView.rowHeight = UITableView.automaticDimension
        commentsTableView.registerNib(cell: CommentsTableViewCell.self)
        logsTableView.registerNib(cell: TicketLogsTableViewCell.self)
        getTicketDetails()
        getTicketLogDetails()
        getTicketCommentDetails()
    }
    
    private func showHideView(count:Int,containerView: UIView){
        let isHide = count == 0
        containerView.isHidden = isHide
    }
    //MARK: -  Ticket Deatil Api 
    private func getTicketDetails(){
        CommonUtilities.showHUD()
        TicketDetailsNetworkService.callApi(id: ticket?.id ?? 0) { (result: Result<TicketDetailsResponseData,Error>) in
            DispatchQueue.main.async {
                CommonUtilities.hideHUD()
                switch result{
                case .success(let responseData):
                    if responseData.apiCode == ApiCode.success.rawValue, let ticketData = responseData.tickets{
                        self.ticket = ticketData
                        self.ticketIDLabel.text = "Ticket ID : \(self.ticket?.id ?? 0)"
                        self.createdByLabel.text = self.ticket?.name
                        self.emailLabel.text = self.ticket?.email
                        self.phoneLabel.text = "\(self.ticket?.phone ?? 0)"
                        self.urgencyLevelLabel.text = self.ticket?.urgencyLevel
                        self.departmentLabel.text = self.ticket?.department?.name
                        self.detailLabel.text = self.ticket?.detail
                        self.statusLabel.text = self.ticket?.status
                        self.toBeAcceptedLabel.text = self.ticket?.toBeAcceptedBy ?? ""
                        //CommonUtilities.changedateFormat(date: self.ticket?.toBeAcceptedBy ?? "", format: Constants.DateFormat.ticketDateFormat, actualFormat: Constants.DateFormat.apiDateFormat2)
                        self.assignedLabel.text = self.ticket?.assignedTo
                        self.showRatingLabel.text = self.ticket?.ticketRating?.rating ?? "No rating available"
                    }else{
                        self.alertWith(title: Constants.AlertTitles.alert, message: responseData.message ?? "")
                    }
                    
                case .failure(let error):
                    self.alertWith(title: "", message: error.localizedDescription)
                }
            }
            
        }
    }
    //MARK: -  Get ticket Log Api 
    private func getTicketLogDetails(){
        CommonUtilities.showHUD()
        TicketLogsNetworkService.callApi(id: ticket?.id ?? 0) { (result: Result<TicketLogDetailsResponseData,Error>) in
            DispatchQueue.main.async {
                CommonUtilities.hideHUD()
                switch result{
                case .success(let responseData):
                    if responseData.apiCode == ApiCode.success.rawValue, let logData = responseData.logs{
                        self.logs = logData
                        self.showHideView(count: self.logs?.count ?? 0, containerView: self.logContainerView)
                        self.logsTableView.reloadData()
                        self.logTableViewHeightConstraint.constant = self.logsTableView.contentSize.height
                    }else{
                        self.alertWith(title: Constants.AlertTitles.alert, message: responseData.message ?? "")
                    }
                    
                case .failure(let error):
                    self.alertWith(title: "", message: error.localizedDescription)
                }
            }
            
        }
    }
    //MARK: -  Get Ticket Api 
    private func getTicketCommentDetails(){
        CommonUtilities.showHUD()
        TicketCommentsNetworkService.callApi(id: ticket?.id ?? 0) { (result: Result<TicketCommentDetailsResponseData,Error>) in
            DispatchQueue.main.async {
                CommonUtilities.hideHUD()
                switch result{
                case .success(let responseData):
                    if responseData.apiCode == ApiCode.success.rawValue, let commentData = responseData.comments{
                        self.comments = commentData
                        self.showHideView(count: self.comments?.count ?? 0, containerView: self.commentsContainerView)
                        self.commentsContainerView.isHidden = self.comments!.count == 0 ? true : false
                        self.commentsTableView.reloadData()
                        self.commentTableViewHeightConstraint.constant = self.commentsTableView.contentSize.height
                    }else{
                        self.alertWith(title: Constants.AlertTitles.alert, message: responseData.message ?? "")
                    }
                    
                case .failure(let error):
                    self.alertWith(title: "", message: error.localizedDescription)
                }
            }
            
        }
    }
}
//MARK: -  Extension 
extension TicketDetailsViewController: UITableViewDelegate, UITableViewDataSource{
    func tableView(_ tableView: UITableView, numberOfRowsInSection section: Int) -> Int {
        if tableView == commentsTableView{
            return comments?.count ?? 0
        }
        return logs?.count ?? 0
    }
    
    func tableView(_ tableView: UITableView, cellForRowAt indexPath: IndexPath) -> UITableViewCell {
        if tableView == commentsTableView{
            let cell:CommentsTableViewCell = tableView.dequeue()
            cell.commentLabel.text = comments?[indexPath.row].body
            cell.addedByLabel.text = comments?[indexPath.row].addedByName
            cell.dateTimeLabel.text = comments?[indexPath.row].createdAt ?? ""
           // cell.dateTimeLabel.text = CommonUtilities.changedateFormat(date: comments?[indexPath.row].createdAt ?? "", format: Constants.DateFormat.ticketDateFormat, actualFormat: Constants.DateFormat.apiDateFormat2)
            return cell
        }
        let cell:TicketLogsTableViewCell = tableView.dequeue()
        cell.byLabel.text = logs?[indexPath.row].by
        cell.createdAtLabel.text = logs?[indexPath.row].createdAt ?? ""
        //CommonUtilities.changedateFormat(date: logs?[indexPath.row].createdAt ?? "", format: Constants.DateFormat.ticketDateFormat, actualFormat: Constants.DateFormat.apiDateFormat2)
        cell.logLabel.text = logs?[indexPath.row].log
        cell.logTypeLabel.text = logs?[indexPath.row].logType
        return cell
    }
    
    func tableView(_ tableView: UITableView, heightForRowAt indexPath: IndexPath) -> CGFloat {
        if tableView == commentsTableView{
            return 100
        }
        else{
        return UITableView.automaticDimension
        }
    }
}
