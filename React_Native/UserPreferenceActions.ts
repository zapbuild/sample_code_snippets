import {
  executeGetRequest,
  executePostRequest
} from '../../utils/FetchUtils';
import { Dispatch } from 'redux';
import { RootState as RootStateType } from '../reducer';
import { setLoading } from '../creators/LoadingCreator';
import {
  setCategories,
  setBrands,
  setPreference
} from '../creators/PreferenceCreators';
import { AppActionTypes } from '../types';
import { UserPrefType } from 'src/types/models/User';

/**
 * 
 * @returns List of categories for the user to select the prefered categories
 */
export const getCategoryList = () => {
  return async (
    dispatch: Dispatch<AppActionTypes>,
    getState: () => RootStateType,
  ) => {
    try {
      dispatch(setLoading(true));
      dispatch(setCategories([]));
      const token = getState().persistedReducer.token;
      const requestPayload = 'dealstore/categories/search?search=level:0&sort=-id&size=30';
      const categoriesResponse = await executeGetRequest(requestPayload, token);
      dispatch(setLoading(false));
      if (categoriesResponse?.code != 200) {
        throw categoriesResponse;
      }
      const categories = categoriesResponse?.response.content;
      dispatch(setCategories(categories));
      return {
        code: categoriesResponse?.response.code,
        payload: categories
      }
    } catch (error) {
      dispatch(setLoading(false));
      return error;
    }
  };
};

/**
 * 
 * @param categoryId id of the category whose brands needs to be fetched
 * @returns List of brands for the specifiied categoryId
 */
export const getBrandList = (categoryId: number) => {
  return async (
    dispatch: Dispatch<AppActionTypes>,
    getState: () => RootStateType,
  ) => {
    try {
      dispatch(setLoading(true));
      const token = getState().persistedReducer.token;
      const brandRequest = `dealstore/mapper/category/brand/search?search=categoryId:${categoryId}`;
      const brandResponse = await executeGetRequest(brandRequest, token);
      dispatch(setLoading(false));
      if (brandResponse?.code != 200) {
        throw brandResponse;
      }
      const brandsList = brandResponse?.response;
      dispatch(setBrands());
      return {
        code: brandResponse?.response.code,
        payload: brandsList
      }
    } catch (error) {
      dispatch(setLoading(false));
      return error;
    }
  };
};

/**
 * 
 * @param preferenceArray Array of selected categories and brands by the user
 * @returns Success/Failure for the store preference request
 */
export const storeCategoryBrandPreference = (preferenceArray: Array<UserPrefType>) => {
  return async (
    dispatch: Dispatch<AppActionTypes>,
    getState: () => RootStateType,
  ) => {
    try {
      dispatch(setLoading(true));
      const { token, userNumber, uuid } = getState().persistedReducer;
      const storePreferenceRequest = `distro/userInfo/${uuid ? uuid : userNumber}/`;
      const storePreferenceResponse = await executePostRequest(storePreferenceRequest, preferenceArray, token);
      dispatch(setLoading(false));
      if (storePreferenceResponse?.code != 200) {
        throw storePreferenceResponse;
      }
      dispatch(setPreference(storePreferenceResponse.response));
      return {
        code: storePreferenceResponse.code
      }
    } catch (err) {
      dispatch(setLoading(false));
      return err;
    }
  };
};
