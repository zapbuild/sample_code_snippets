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