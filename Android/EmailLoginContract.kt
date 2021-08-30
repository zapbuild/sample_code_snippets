package com.tokr.com.ui.login.emailLogin

import androidx.annotation.StringRes
import com.tokr.com.data.model.login.LoginBean
import com.tokr.com.data.model.emailLogin.EmailRequest
import com.tokr.com.ui.base.BasePresenter
import com.tokr.com.ui.base.BaseView

/**
 * <h1>Email Login Contract<h1>
 *
 * <p>This class contains all the methods of activity and presenter </p>
 *
 */


interface EmailLoginContract {

    interface View : BaseView {

        fun showEmailError(@StringRes msg: Int)

        fun hideEmailError()

        fun showPasswordError(@StringRes msg: Int)

        fun hidePasswordError()

        fun enableSubmitButton()

        fun disableSubmitButton()

        fun onSuccess(response: LoginBean)

        fun onFailure(message: String)

        fun moveToOtpScreen()

        fun onError()

    }

    interface Presenter : BasePresenter {
        fun login(request: EmailRequest)
    }
}