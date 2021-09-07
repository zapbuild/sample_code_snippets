// Create Mock Store for Redux
import configureMockStore from 'redux-mock-store';
import thunk from 'redux-thunk';
import fetchMock from 'fetch-mock';
import {
  LOADING_STATUS,
  GET_CATEGORIES,
  GET_BRANDS,
  SET_PREFERENCE
} from '../src/redux/types';
import {
  getCategoryList,
  getBrandList,
  storeCategoryBrandPreference,
  getCategoryBrandPreference
} from '../src/redux/actions/PreferenceActions';
import { Log } from '../src/utils/Logger';
import { app_base_url } from '../src/Security';

const middlewares = [thunk];
const mockReduxStore = configureMockStore(middlewares);

describe('PREFERENCE_ACTIONS TESTS', () => {
  afterEach(() => {
    fetchMock.restore();
  });

  it('GET_CATEGORIES SUCCESS', () => {
    fetchMock.getOnce(
      `${app_base_url}/dealstore/categories/search?search=level:0&sort=-id&size=30`,
      {
        body: {
          content: [
            {
              id: 5740,
              name: 'Gift Cards',
              label: '',
              topCategoryId: 0,
              vendorId: 1,
              catFullPathId: '/Gift Cards',
              level: 0,
              url: 'https://www.amazon.in/s?i=gift-cards&rh=p_85%3A10440599031',
              filters: null,
              frequency: 180,
              active: 1,
              categoryLogo: '',
              createTimestamp: '2020-05-09 04:53:38',
              updateTimestamp: '2020-06-26 08:23:37',
              valid: false,
              preference: 0,
            },
          ],
        },
        status: 200,
        headers: { 'content-type': 'application/json' },
      },
    );

    const expectedActions = [
      { type: LOADING_STATUS, payload: true },
      { type: GET_CATEGORIES, payload: [] },
      { type: LOADING_STATUS, payload: false },
      {
        type: GET_CATEGORIES,
        payload: [
          {
            id: 5740,
            name: 'Gift Cards',
            label: '',
            topCategoryId: 0,
            vendorId: 1,
            catFullPathId: '/Gift Cards',
            level: 0,
            url: 'https://www.amazon.in/s?i=gift-cards&rh=p_85%3A10440599031',
            filters: null,
            frequency: 180,
            active: 1,
            categoryLogo: '',
            createTimestamp: '2020-05-09 04:53:38',
            updateTimestamp: '2020-06-26 08:23:37',
            valid: false,
            preference: 0,
          },
        ],
      },
    ];
    const store = mockReduxStore({
      persistedReducer: {
        token: 'token',
      },
    });
    const res: any = getCategoryList();
    return store.dispatch(res).then(() => {
      expect(store.getActions()).toEqual(expectedActions);
    });
  });

  it('GET_CATEGORIES TOKEN_ERROR', () => {
    fetchMock.getOnce(
      `${app_base_url}/dealstore/categories/search?search=level:0&sort=-id&size=30`,
      {
        body: {
          timestamp: 1591007690656,
          path: '/dealstore/categories/search',
          status: 500,
          error: 'Internal Server Error',
          message: 'Expired JWT',
        },
        status: 500,
        headers: { 'content-type': 'application/json' },
      },
    );
    const store = mockReduxStore({
      persistedReducer: {
        token: undefined,
      },
    });
    const res: any = getCategoryList();
    return store.dispatch(res).then(async (res: any) => {
      const error = JSON.parse(await res.error);
      Log(error, "this is error");
      expect(error.status).toEqual(500);
    });
  });

  it('GET_BRANDS SUCCESS', () => {
    const catId = 1;
    fetchMock.getOnce(
      `${app_base_url}/dealstore/mapper/category/brand/search?search=categoryId:${catId}`,
      {
        body: [
          {
            category_id: 1,
            category_name: 'Clothing & Accessories',
            brands: [
              {
                id: 7,
                name: 'Workout',
                rating: 0,
                preference: -1,
                logoUrl: 'http://NA.na',
                createTimestamp: '2020-05-31 14:31:04',
                updateTimestamp: '2020-05-31 14:31:04',
              },
            ],
          },
        ],
        status: 200,
        headers: { 'content-type': 'application/json' },
      },
    );

    const expectedActions = [
      { type: LOADING_STATUS, payload: true },
      { type: LOADING_STATUS, payload: false },
      { type: GET_BRANDS },
    ];
    const store = mockReduxStore({
      persistedReducer: {
        token: 'token',
      },
    });
    const res: any = getBrandList(catId);
    return store.dispatch(res).then(() => {
      expect(store.getActions()).toEqual(expectedActions);
    });
  });

  it('GET_BRANDS TOKEN_ERROR', () => {
    const catId = 1;
    fetchMock.getOnce(
      `${app_base_url}/dealstore/mapper/category/brand/search?search=categoryId:${catId}`,
      {
        body: {
          timestamp: 1591007690656,
          path: '/dealstore/categories/search',
          status: 500,
          error: 'Internal Server Error',
          message: 'Expired JWT',
        },
        status: 500,
        headers: { 'content-type': 'application/json' },
      },
    );
    const store = mockReduxStore({
      persistedReducer: {
        token: undefined,
      },
    });
    const res: any = getBrandList(catId);
    return store.dispatch(res).then(async (res: any) => {
      const error = JSON.parse(await res.error);
      expect(error.status).toEqual(500);
    });
  });

  it('SET_PREFERENCE SUCCESS', () => {
    fetchMock.postOnce(
      `${app_base_url}/distro/userInfo/919623716602/`,
      {
        body: [
          {
            preferredCategory: 1,
            preferredBrands: [1, 2],
          },
          {
            preferredCategory: 2,
            preferredBrands: [1, 2, 3],
          },
        ],
        status: 200,
        headers: { 'content-type': 'application/json' },
      },
    );

    const expectedActions = [
      { type: LOADING_STATUS, payload: true },
      { type: LOADING_STATUS, payload: false },
      {
        type: SET_PREFERENCE,
        payload: {
          preference: [
            {
              preferredCategory: 1,
              preferredBrands: [1, 2],
            },
            {
              preferredCategory: 2,
              preferredBrands: [1, 2, 3],
            },
          ],
        },
      },
    ];
    const store = mockReduxStore({
      persistedReducer: {
        token: 'token',
        userNumber: 919623716602,
      },
    });

    const mockParams = [
      {
        preferredCategory: 1,
        preferredBrands: [1, 2],
      },
      {
        preferredCategory: 2,
        preferredBrands: [1, 2, 3],
      },
    ];
    const res: any = storeCategoryBrandPreference(mockParams);
    return store.dispatch(res).then(() => {
      expect(store.getActions()).toEqual(expectedActions);
    });
  });

  it('SET_PREFERENCE TOKEN_ERROR', () => {
    fetchMock.postOnce(
      `${app_base_url}/distro/userInfo/919623716602/`,
      {
        body: {
          timestamp: 1591007690656,
          path: '/dealstore/categories/search',
          status: 500,
          error: 'Internal Server Error',
          message: 'Expired JWT',
        },
        status: 500,
        headers: { 'content-type': 'application/json' },
      },
    );

    const store = mockReduxStore({
      persistedReducer: {
        token: undefined,
        userNumber: 919623716602,
      },
    });

    const mockParams = [
      {
        preferredCategory: 1,
        preferredBrands: [1, 2],
      },
    ];
    const res: any = storeCategoryBrandPreference(mockParams);
    return store
      .dispatch(res)
      .then(async (res: any) => {
        if (res.error) {
          const error = JSON.parse(await res.error);
          expect(error.status).toEqual(500);
        }
      });
  });

  it('GET_CATEGORY_BRAND_PREFERENCE SUCCESS', () => {
    fetchMock.getOnce(
      `${app_base_url}/distro/userInfo/919623716602/`,
      {
        body: [
          {
            preferredCategory: 1,
            preferredBrands: [1, 2],
          },
          {
            preferredCategory: 2,
            preferredBrands: [1, 2, 3],
          },
        ],
        status: 200,
        headers: { 'content-type': 'application/json' },
      },
    );

    const expectedActions = [
      { type: LOADING_STATUS, payload: true },
      { type: LOADING_STATUS, payload: false },
      {
        type: SET_PREFERENCE,
        payload: {
          preference: [
            {
              preferredCategory: 1,
              preferredBrands: [1, 2],
            },
            {
              preferredCategory: 2,
              preferredBrands: [1, 2, 3],
            },
          ],
        },
      },
    ];
    const store = mockReduxStore({
      persistedReducer: {
        token: 'token',
        userNumber: 919623716602,
      },
    });
    const res: any = getCategoryBrandPreference();
    return store.dispatch(res).then(() => {
      expect(store.getActions()).toEqual(expectedActions);
    });
  });

  it('GET_CATEGORY_BRAND_PREFERENCE TOKEN_ERROR', () => {
    fetchMock.getOnce(
      `${app_base_url}/distro/userInfo/919623716602/`,
      {
        body: {
          timestamp: 1591007690656,
          path: '/dealstore/categories/search',
          status: 500,
          error: 'Internal Server Error',
          message: 'Expired JWT',
        },
        status: 500,
        headers: { 'content-type': 'application/json' },
      },
    );

    const store = mockReduxStore({
      persistedReducer: {
        token: undefined,
        userNumber: 919623716602,
      },
    });
    const res: any = getCategoryBrandPreference();
    return store
      .dispatch(res)
      .then(async (res: any) => {
        if (res.error) {
          const error = JSON.parse(await res.error);
          expect(error.status).toEqual(500);
        }
      });
  });
});
