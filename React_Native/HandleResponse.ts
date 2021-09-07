import { Log } from './Logger';
import { AUTH_ERROR } from '../redux/types';
import store from '../redux/reducer';

/**
 * 
 * @param apiResponse 
 * @returns Single Log statement for API requests and middleware to interscept AUTH ERROR
 */
export const checkResponse = (apiResponse: Response) => {
  apiResponse.clone().json().then(response => {
    Log(`Response for ${apiResponse.url}, code = ${apiResponse.status}`, response);
    if (apiResponse.status == 500) {
      store.dispatch({ type: AUTH_ERROR, payload: "JWT Error" });
    }
  });
};
