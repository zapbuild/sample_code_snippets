import { checkResponseStatus } from './HandleResponse';
import NetInfo from '@react-native-community/netinfo';
import Config from './Config';

/**
 * 
 * @param endpoint POST Request endpoint
 * @param paramsObject Request Params
 * @param token Request Sesssion Token
 * @param isUrlEncoded Request url encoded
 * @returns Utility function for executing Post requests throughout the apps
 */
export const executePostRequest = async (
  endpoint: string,
  paramsObject: Object,
  token?: string,
  isUrlEncoded = false,
) => {
  try {
    const networkStatus = await NetInfo.fetch();
    if (!networkStatus.isConnected) {
      return {
        code: 400,
        error: [{ error: Config.error.error_internet_connection }],
      };
    }
    let requestFormBody = isUrlEncoded ? encodeParamsObject(paramsObject) : [];
    const request = await fetch(`${Config.server.base_url}/${endpoint}`, {
      method: 'POST',
      headers: getAPIHeader(token, isUrlEncoded),
      body: isUrlEncoded ? requestFormBody : JSON.stringify(paramsObject),
    });
    checkResponseStatus(request);
    if (request.status != 200) {
      return {
        code: request.status,
        error: request.text(),
      };
    }
    const response = await request.json();
    return {
      code: request.status,
      response,
    };
  } catch (error) {
    return {
      code: 400,
      error,
    };
  }
};

/**
 * 
 * @param endpoint Get Request endpoint
 * @param token Request Session token
 * @returns Utility function for executing Get requests throughout the apps
 */
export const executeGetRequest = async (endpoint: string, token?: string) => {
  try {
    const netInfoStatus = await NetInfo.fetch();
    if (!netInfoStatus.isConnected) {
      return {
        code: 400,
        error: [{ error: Config.error.error_internet_connection }],
      };
    }
    const getResponse = await fetch(`${Config.server.base_url}/${endpoint}`, {
      method: 'GET',
      headers: getAPIHeader(token),
    });
    checkResponseStatus(getResponse);
    if (getResponse.status != 200) {
      return {
        code: getResponse.status,
        error: getResponse.text(),
      };
    }
    const response = await getResponse.json();
    return {
      code: getResponse.status,
      response: response,
    };
  } catch (error) {
    return {
      code: 400,
      error
    };
  }
};

/**
 * 
 * @param token 
 * @param isUrlEncoded 
 * @returns header object for Post request
 */
const getAPIHeader = (token?: string, isUrlEncoded?: boolean) => {
  return {
    "Access-Control-Allow-Origin": "*",
    Accept: 'application/json',
    'Content-Type': isUrlEncoded
      ? 'application/x-www-form-urlencoded'
      : 'application/json',
    authorization: token ? 'Bearer ' + token : '',

    'X-app-name': 'frontend',
  };
};

/**
 * 
 * @param paramsObject 
 * @returns Encoded Params object
 */
const encodeParamsObject = (paramsObject: Object) => {
  let formBody = [];
  for (let property in paramsObject) {
    let encodedKey = encodeURIComponent(property);
    let encodedValue = encodeURIComponent(paramsObject[property]);
    formBody.push(encodedKey + '=' + encodedValue);
  }
  return formBody.join('&');
};
