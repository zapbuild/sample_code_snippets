import UIKit
/**
 TicketListViewController.swift
 Team Square
 
 - Author:
 Poonam Chandel
 
 - Copyright:
 Zapbuild Technologies Pvt Ltd
 
 - Date:
 20/07/22
 
 - Version:
 1.0
 */
class TicketListViewController: BaseViewController {
    //MARK: -  Outlets and Variables 
    @IBOutlet weak var ticketsTableView: UITableView!
    @IBOutlet weak var navigationBarView: CustomNavigationBar!
    @IBOutlet weak var statusFilterContainerView: UIView!
    @IBOutlet weak var optionMenuView: Menu!
    
    private let pageSize = 20
    private let page = 1
    private let status = 0
    private var tickets: Tickets? = Tickets()
    private var ticketList : [TicketResults] = []
    private var totalPage:Int? = 1
    private var currentPage = 1
    
    //MARK: -  View Controller Life Cycle Methods 
    override func viewDidLoad() {
        super.viewDidLoad()
        configure()
    }
    
    override func viewWillAppear(_ animated: Bool) {
        super.viewWillAppear(animated)
        self.navigationController?.isNavigationBarHidden = true
        self.navigationController?.setStatusBar(backgroundColor: .appBlue!)
        self.navigationController?.navigationBar.setNeedsLayout()
        ticketsTableView.reloadData()
    }
    //MARK: -  Button Actions 
    @IBAction func statusFilterButtonTapped(_ sender: UIButton) {
        switch sender.tag {
        case 0:
            self.navigationBarView.rightNavigationBarButton.setTitle("All Status", for: .normal)
        case 1:
            self.navigationBarView.rightNavigationBarButton.setTitle("Pending", for: .normal)
        case 2:
            self.navigationBarView.rightNavigationBarButton.setTitle("In - Progress", for: .normal)
        case 4:
            self.navigationBarView.rightNavigationBarButton.setTitle("Completed", for: .normal)
        case 5:
            self.navigationBarView.rightNavigationBarButton.setTitle("Closed", for: .normal)
        default:
            break
        }
        ticketList = []
        getTicketList(status: (sender.tag), page: page)
        self.statusFilterContainerView.isHidden =  true
        
    }
    @IBAction func addNewTicketButtonTapped(_ sender: UIButton) {
        let newTicketVC: NewTicketViewController = getInstance(storyboard: .helpdesk)!
        self.navigationController?.pushViewController(newTicketVC, animated: true)
    }
    //MARK: -  UI Uodate 
    private func configure(){
        navigationBarView.navigationTitleLabel.text = "Tickets"
        navigationBarView.sideMenuIconImageView.image = UIImage(named: "Menu")!
        navigationBarView.sideMenuButtonPressed = {
            self.revealViewController()?.revealSideMenu()
        }
        navigationBarView.rightNavigationBarButton.isHidden = false
        navigationBarView.rightButtonPressed = {
            self.statusFilterContainerView.isHidden =  !self.statusFilterContainerView.isHidden
        }
        navigationBarView.rightNavigationBarButton.setTitle("All Status", for: .normal)
        ticketsTableView.registerNib(cell: TicketListTableViewCell.self)
        getTicketList(status: 0, page: currentPage)
    }
    //MARK: -  Ticket list Api 
    private func getTicketList(status:Int,refresh:Bool? = false,page:Int){
        
        if refresh!{
            self.ticketsTableView.beginRefreshing()
        }
        
        let parameters : [String:Any] = [
            "page" : page,
            "status" : status,
            "page_size" : pageSize
            
        ]
        CommonUtilities.showHUD()
        MyTicketsNetworkService.callApi(parameters: parameters) { (result: Result<TicketsResponseData,Error>) in
            DispatchQueue.main.async {
                CommonUtilities.hideHUD()
                switch result{
                case .success(let responseData):
                    if responseData.apiCode == ApiCode.success.rawValue, let ticketData = responseData.tickets{
                        self.tickets = ticketData
                        if refresh!{
                            self.ticketList.removeAll()
                            self.ticketsTableView.endRefreshing()
                        }
                        for i in 0..<(self.tickets?.results?.count ?? 0){
                            self.ticketList.append((self.tickets?.results?[i])!)
                        }
                        self.totalPage = (self.tickets?.count ?? 0)/self.pageSize
                        self.ticketsTableView.reloadData()
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
extension TicketListViewController: UITableViewDelegate, UITableViewDataSource{
    func tableView(_ tableView: UITableView, numberOfRowsInSection section: Int) -> Int {
        return /*tickets?.results?.count ?? 0*/ ticketList.count
    }
    
    func tableView(_ tableView: UITableView, cellForRowAt indexPath: IndexPath) -> UITableViewCell {
        
        if (currentPage<totalPage!) && (indexPath.row == (ticketList.count)-1){
            let cell = tableView.dequeueReusableCell(withIdentifier: "loading")
            return cell!
        }else{
            let cell:TicketListTableViewCell = tableView.dequeue()
            cell.idLabel.text = "\(ticketList[indexPath.row].id ?? 0)"
            cell.ticketDetailLabel.text = "\(ticketList[indexPath.row].detail ?? "")"
            cell.urgencyLevelLabel.text = "\(ticketList[indexPath.row].urgencyLevel ?? "")"
            cell.statusLabel.text = "\(ticketList[indexPath.row].status ?? "")"
            cell.assignedToLabel.text = "\(ticketList[indexPath.row].assignedTo ?? "")"
            cell.buttonPressed = {
                /*let ticketRatingVC:TicketRatingViewController = self.getInstance(storyboard: .helpdesk)!
                ticketRatingVC.ticketResults = self.tickets?.results?[indexPath.row]
                self.navigationController?.present(ticketRatingVC, animated: true)*/
                cell.threeDotsOptionView.isHidden =  !cell.threeDotsOptionView.isHidden
            }
            cell.threeDotsOptionView.optionButtonPressed = {
                let ticketRatingVC:TicketRatingViewController = self.getInstance(storyboard: .helpdesk)!
                ticketRatingVC.ticketResults = self.tickets?.results?[indexPath.row]
                self.navigationController?.present(ticketRatingVC, animated: true)
                cell.threeDotsOptionView.isHidden = true
            }
            return cell
        }
    }
    
    func tableView(_ tableView: UITableView, didSelectRowAt indexPath: IndexPath) {
        let ticketDetailsVC: TicketDetailsViewController = getInstance(storyboard: .helpdesk)!
        ticketDetailsVC.ticket = self.tickets?.results?[indexPath.row]
        self.navigationController?.pushViewController(ticketDetailsVC, animated: true)
    }
    
    func tableView(_ tableView: UITableView, willDisplay cell: UITableViewCell, forRowAt indexPath: IndexPath) {
        if (currentPage<totalPage!) && indexPath.row == ticketList.count-1 {
           currentPage = currentPage + 1
            getTicketList(status: status,refresh: false, page: currentPage)
        }
    }
}
