package com.tokr.com.ui.login.emailLogin

import android.text.TextUtils
import com.tokr.com.Constants.PASSWORD_MIN_LEN
import com.tokr.com.R
import com.tokr.com.data.api.ApiClient
import com.tokr.com.data.api.ApiCodes
import com.tokr.com.data.model.emailLogin.EmailRequest
import com.tokr.com.ui.base.impl.BasePresenterImpl
import com.tokr.com.util.EmailValidator
import io.reactivex.android.schedulers.AndroidSchedulers
import io.reactivex.disposables.CompositeDisposable
import io.reactivex.schedulers.Schedulers

/**
 * <h1>Email Login Presenter<h1>
 *
 * <p>This class contains all the API calls for email login and methods for email validations </p>
 *
 */

class EmailLoginPresenter(private var view: EmailLoginContract.View) : BasePresenterImpl(view), EmailLoginContract.Presenter {

    private var compositeDisposable: CompositeDisposable? = CompositeDisposable()
    private var isEmailValid = false
    private var isPasswordValid = false

    override fun onDestroy() {
        compositeDisposable?.clear()
    }

    override fun login(request: EmailRequest) {

        if (!isValidInputs())
            return

        view.showContentLoading()
        compositeDisposable?.add(ApiClient.getInstance().emailLogin(request)
                .subscribeOn(Schedulers.io())
                .observeOn(AndroidSchedulers.mainThread())
                .subscribe({ loginModel ->
                    view.hideContentLoading()
                    if (loginModel.status == ApiCodes.API_SUCCESS) {
                        if (loginModel.code == ApiCodes.API_SUCCESS_NEW_USER)
                            view.moveToOtpScreen()
                        else {
                            val data = loginModel.data
                            view.onSuccess(data)
                        }
                    } else if (loginModel.status == ApiCodes.API_FAILURE) {
                        if (loginModel.code == ApiCodes.USER_NOT_VERIFIED) {
                            view.moveToOtpScreen()
                        } else
                            view.onFailure(loginModel.message[0].response)
                    }
                }, {
                    view.hideContentLoading()
                    this.popupErrorHandler(it)
                    view.onError()
                }))
    }

    private fun isValidInputs(): Boolean {
        return isEmailValid && isPasswordValid
    }

    fun isValidEmail(email: String) {
        view.disableSubmitButton()
        if (TextUtils.isEmpty(email)) {
            view.showEmailError(R.string.error_msg_empty_email)
        } else if (!EmailValidator.isValidEmail(email)) {
            view.showEmailError(R.string.error_msg_invalid_email)
        } else {
            isEmailValid = true
            view.hideEmailError()
            if (isPasswordValid)
                view.enableSubmitButton()
        }
    }

    fun isValidPassword(password: String) {
        view.disableSubmitButton()
        if (TextUtils.isEmpty(password)) {
            view.showPasswordError(R.string.error_msg_empty_password)
        } else if (password.length < PASSWORD_MIN_LEN) {
            view.showPasswordError(R.string.error_msg_password_len)
        } else {
            isPasswordValid = true
            view.hidePasswordError()
            if (isEmailValid)
                view.enableSubmitButton()
        }
    }
}