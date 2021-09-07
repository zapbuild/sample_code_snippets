// *****************************************Root Module********************************************************************
import { GraphQLError } from 'graphql';
import { GraphQLModule } from '@nestjs/graphql';
import { ScheduleModule } from '@nestjs/schedule';
import { Module, CacheModule } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { errorType } from '@common';

import { AppService } from './app.service';
import { AppController } from './app.controller';
import { RolesModule } from './app/modules/role/roles.module';
import { AdminModule } from './app/modules/admin/admin.module';
import { campaignModule } from './app/modules/campaign/campaign.module';
import { MediaOwnerModule } from './app/modules/mediaOwner/mediaOwner.module';
import { PlayerModule } from './app/modules/player/player.module';
import { DriversModule } from './app/modules/driver/drivers.module';
import { ReportModule } from './app/modules/report/report.module';
import { LinksModule } from './app/modules/links/links.module';
import { CMSModule } from './app/modules/cms/cms.module';
import { CacheService } from './core/cache';

const errorResponse: any = {};
const getErrorCode = (errorName) => {
  errorName = errorName.split(' ')[1];

  return errorType[errorName];
};

@Module({
  imports: [
    GraphQLModule.forRoot({
      autoSchemaFile: 'schema.gql',
      installSubscriptionHandlers: true,
      buildSchemaOptions: {
        numberScalarMode: 'integer',
      },
      formatError: (error: GraphQLError) => {
        (errorResponse.status = getErrorCode(error.message)),
          (errorResponse.message = error.message);
        errorResponse.code = error?.extensions?.code || 'INTERNAL_SERVER_ERROR';
        return errorResponse;
      },
    }),
    CacheModule.registerAsync({
      useClass: CacheService,
    }),
    TypeOrmModule.forRoot(),
    ScheduleModule.forRoot(),
    CMSModule,
    AdminModule,
    RolesModule,
    LinksModule,
    DriversModule,
    campaignModule,
    PlayerModule,
    ReportModule,
    MediaOwnerModule,
  ],
  controllers: [AppController],
  providers: [AppService],
})
export class AppModule {}



// ********************************************   Resolver File  *****************************************************************
@Resolver((of) => AdminEntity)
export class AdminResolver {
  constructor(private readonly adminService: AdminService) {}
  /**
* Operating Area Details
*
* @remarks
* This method is part of the Operating Area.
* It Caters the Player (Media Owner) & Admins need to view detail of Operating Area*
* Scope For all
*	@param areaId - 1 input : operating area UUID

* @returns custom OperatingAreaResponse
* * 
*/
  @Query(() => OperatingAreaResponse, { nullable: true })
  async fetchOperatingAreaById(@Args("areaId") areaId: string): Promise<any> {
    return await this.adminService.getOperatingAreaById(areaId);
  }
}

// *****************************************      Service File     *****************************************************8 

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

//***********************************Sample Entity******************************* */
import {
    Entity,
    Column,
    OneToOne,
    ManyToOne,
    Timestamp,
    OneToMany,
    JoinColumn,
    CreateDateColumn,
    UpdateDateColumn,
    PrimaryGeneratedColumn,
  } from 'typeorm';
  import { CartEntity } from './cart.entity';
  import { DeviceEntity } from './device.entity';
  import { DeviceDelivery } from './deviceDelivery.entity';
  import { DriverEntity } from './driver.entity';
  import { MediaOwnerEntity } from './mediaOwner.entity';
  import { OfferEntity } from './offer.entity';
  import { OperatingArea } from './operatingArea.entity';
  import { PlayerType } from './playerType.entity';
  import { VehicleEntity } from './vehicle.entity';
  
  export enum Status {
    inCart,
    offerOpen,
    subscribed,
    available,
  }
  
  @Entity('player')
  export class PlayerEntity {
    @PrimaryGeneratedColumn('uuid')
    id: string;
    @Column({
      type: 'enum',
      enum: Status,
      default: Status.available,
    })
    status: Status;
  
    @Column({
      nullable: true,
      default: null,
    })
    statusDetailId: Status; // OfferId/ OrderId/ cartId
    @Column({
      nullable: true,
    })
    comment: string;
  
    @Column({ default: true })
    isActive: boolean;
    @Column({
      nullable: true,
      default: 'default',
    })
    channel: string;
  
    @ManyToOne(() => PlayerType, (playerType) => playerType.player)
    @JoinColumn({ name: 'playerType' })
    playerType: PlayerType;
    @Column({ type: 'timestamp', default: null })
    purchaseDate: string;
    @CreateDateColumn({
      nullable: false,
      name: 'createdAt',
    })
    createdAt: Timestamp;
  
    @UpdateDateColumn({
      nullable: false,
      name: 'updatedAt',
    })
    updatedAt: Timestamp;
  
    @OneToOne(() => DeviceEntity)
    @JoinColumn({ name: 'currentDeviceId' })
    currentDeviceId: DeviceEntity;
  
    @OneToOne(() => VehicleEntity)
    @JoinColumn({ name: 'currentVehicleId' })
    currentVehicleId: VehicleEntity;
  
    @OneToOne(() => DriverEntity)
    @JoinColumn({ name: 'currentDriverId' })
    currentDriverId: DriverEntity;
  
    @OneToMany(() => CartEntity, (cart) => cart.player)
    cart: CartEntity;
  
    @OneToMany(() => OfferEntity, (offer) => offer.player)
    offer: OfferEntity;
  
    @OneToMany(() => DeviceDelivery, (deviceDelivery) => deviceDelivery.player)
    deviceDelivery: DeviceDelivery;
  
    @ManyToOne(
      () => OperatingArea,
      (operatingArea: OperatingArea) => operatingArea.player,
      { onUpdate: 'CASCADE', onDelete: 'CASCADE' },
    )
    public operatingArea: OperatingArea;
  
    @OneToOne(() => MediaOwnerEntity)
    @JoinColumn({ name: 'currentMediaOwnerId' })
    currentMediaOwnerId: MediaOwnerEntity;
  }
  