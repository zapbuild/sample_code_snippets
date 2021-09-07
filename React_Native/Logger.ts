/**
 * 
 * @param params 
 * @returns A custom Logger function to print only on DEV mode and not in Release/Production
 */
export const Log = (...params: any) => {
  if (__DEV__) {
    console.log({ ...params });
  }
};
