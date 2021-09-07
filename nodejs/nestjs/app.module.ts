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
