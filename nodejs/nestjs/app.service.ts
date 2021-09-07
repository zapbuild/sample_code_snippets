@Injectable()
export class AdminService {
  constructor(
    @InjectRepository(OperatingArea)
    private readonly areaRepository: Repository<OperatingArea>,
    @InjectRepository(Config)
    private readonly configRepository: Repository<Config>
  ) {}

  // fetch operating area & attached  billboard details
  async getOperatingAreaById(areaId) {
    if (!areaId) {
      throw new ApolloError(errorName.BAD_USER_INPUT);
    } else {
      const mediaShare = await this.configRepository
        .createQueryBuilder("config")
        .select("factor", "impressionCostPerK")
        .where("config.constant = :mediashare", {
          mediashare: MEDIA_OWNER_SHARE,
        })
        .getRawOne();
      const hst = await this.configRepository
        .createQueryBuilder("config")
        .select("factor", "impressionCostPerK")
        .where("config.constant = :hst", {
          hst: HST,
        })
        .getRawOne();

      const area: any = await this.areaRepository
        .createQueryBuilder("area")
        .andWhere("area.id = :id", { id: areaId })
        .getOne();

      if (area) {
        area.hst = hst;
        if (area.image) {
          // fetch Presigned Image url
          area.image = await fetchUrl(area.image, AWS_S3_BUCKET_USER);
        }
        // fetch All Players  in this area
        const players = await this.getPlayerByOperatingArea(areaId);

        let availableBillboard = 0;
        players?.forEach((p) => {
          if (!p.currentDriverId) {
            availableBillboard++;
          }
        });
        area.totalBillboard = players.length ? players.length : "0";
        area.availableBillboard = availableBillboard;

        // fetch all zones & their cpv and get average
        const averageCpv = await this.getCpvOperatingArea(areaId);
        //  cpv * Impression per month * % share of media  owner
        const ownersMonthlyShare =
          area.impression * averageCpv * parseInt(mediaShare);
        area.ownersMonthlyShare = ownersMonthlyShare;
        // total quarters
        const quarters = Math.ceil(area.term ? area.term / 3 : 0);

        // ROI Details
        area.OperatingAreaROI = await this.ROICalculator(
          quarters,
          ownersMonthlyShare,
          area.cost
        );
        // CPV Details
        area.OperatingAreaCpv = {
          averageCPV: averageCpv,
          text: area.cpvText,
          title: area.cpvTitle,
        };
        // Impression Details
        area.OperatingAreaImpressions = {
          impression: area.impression,
          text: area.impressionText,
          title: area.impressionTitle,
        };
        // Subscription Package details
        area.OperatingAreaSubscriptionTerm = {
          term: area.term,
          text: area.termText,
          title: area.termTitle,
        };
        // Sbscription Cost
        area.OperatingAreaSubscriptionCost = {
          cost: area.cost,
          text: area.costText,
          title: area.costTitle,
        };
      }

      return area;
    }
  }
}
