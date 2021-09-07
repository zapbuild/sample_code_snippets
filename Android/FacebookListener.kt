package com.code.utils.manager.facebook


import androidx.annotation.StringRes
import com.code.data.model.SignUpRequest

/**
 * <h1>Fb SignIn Completion Listener </h1>
 *
 *
 * <p>This class contains methods for facebook success and failures</p>
 *
 */


interface FacebookListener {

    fun onFacebookLoginSuccess(signUpRequest: SignUpRequest)

    fun onFacebookLoginError(@StringRes message: Int)

}
