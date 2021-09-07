package com.code.utils.manager.facebook

import android.os.Bundle
import com.facebook.*
import com.facebook.login.LoginManager
import com.facebook.login.LoginResult
import com.zvestapro.R
import com.code.base.BaseActivity
import com.code.data.model.SignUpRequest
import com.code.utils.Constants.*
import org.json.JSONException
import org.json.JSONObject
import timber.log.Timber

/**
 * <h>Facebook Signin Helper</h>
 *
 * <p>This class is handling facebook sign in request parameters,process, success and failure</p>
 *
 */

class FacebookManager(var activity: BaseActivity) : FacebookCallback<LoginResult>,
    GraphRequest.GraphJSONObjectCallback {

    private var listener: FacebookListener? = null
    private var accessToken: String? = null
    private var callbackManager: CallbackManager? = null
    private var loginManager: LoginManager? = null

    init {
        callbackManager = CallbackManager.Factory.create()
        loginManager = LoginManager.getInstance()
        loginManager?.registerCallback(callbackManager, this)
    }

    fun setListener(listener: FacebookListener): FacebookManager {
        this.listener = listener
        return this
    }

    fun login() {
        loginManager?.logInWithReadPermissions(activity, listOf(Constants.PUBLIC_PROFILE, Constants.EMAIL))
    }

    override fun onSuccess(loginResult: LoginResult) {
        loginResult.accessToken

        accessToken = loginResult.accessToken.token
        if (loginResult.recentlyDeniedPermissions.contains(Constants.EMAIL)) {
            return
        }
        val request = GraphRequest.newMeRequest(loginResult.accessToken, this)
        val parameters = Bundle()
         parameters.putString(Constants.FIELDS, "Constants.NAME,Constants.PICTURE,Constants.EMAIL,Constants.FIRST_NAME,Constants.LAST_NAME")
        request.parameters = parameters
        request.executeAsync()
    }

    override fun onCancel() {
        //when fb login cancelled by the user
        listener?.onFacebookLoginError(R.string.error_msg_fb_error)
    }

    override fun onError(error: FacebookException) {
        Timber.d(error)
        if (error is FacebookAuthorizationException) {
            if (AccessToken.getCurrentAccessToken() != null) {
                LoginManager.getInstance().logOut()
            }
        }
        listener?.onFacebookLoginError(R.string.error_msg_fb_error)
    }

    override fun onCompleted(jsonObject: JSONObject, response: GraphResponse) {
        val error = response.error
        val signUpRequest = SignUpRequest()
        if (error != null) {
            //report error to the listener
            listener?.onFacebookLoginError(R.string.error_msg_fb_error)
            return
        }

        if (!jsonObject.has("id")) {
            //show prompt to the user to provide the email
            listener?.onFacebookLoginError(R.string.error_msg_fb_error)
            return
        }

        try {
            if (jsonObject.has("email"))
                signUpRequest.email = jsonObject.optString("email")
            if (jsonObject.has("first_name"))
                signUpRequest.firstName = jsonObject.optString("first_name")
            if (jsonObject.has("last_name"))
                signUpRequest.lastName = jsonObject.optString("last_name")
            signUpRequest.providerId = jsonObject.optString("id")
            signUpRequest.providerName = PROVIDER_FACEBOOK
            listener?.onFacebookLoginSuccess(signUpRequest)

        } catch (e: JSONException) {
            Timber.d(e)
            e.printStackTrace()
            listener?.onFacebookLoginError(R.string.error_msg_fb_error)
        }

    }

    fun getcallBackManager(): CallbackManager? {
        return callbackManager
    }
}