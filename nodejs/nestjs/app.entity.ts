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
  