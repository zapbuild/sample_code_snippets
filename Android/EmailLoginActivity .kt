package com.tokr.com.ui.login.emailLogin

import android.Manifest
import android.app.Activity
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Bundle
import androidx.core.app.ActivityCompat
import android.text.InputFilter
import android.view.View
import com.tokr.com.Constants.DISCOVER_SCREEN
import com.tokr.com.Constants.EMAIL_MAX_LENGTH
import com.tokr.com.Constants.PROFILE_SCREEN
import com.tokr.com.R
import com.tokr.com.data.local.PrefManager
import com.tokr.com.data.model.login.LoginBean
import com.tokr.com.data.model.emailLogin.EmailRequest
import com.tokr.com.ui.base.BaseActivity
import com.tokr.com.ui.forgotPassword.ForgotPasswordActivity
import com.tokr.com.ui.forYou.ForYouActivity
import com.tokr.com.ui.onboarding.OnBoardingActivity
import com.tokr.com.ui.profile.ProfileActivity
import com.tokr.com.ui.verifyOtp.VerifyOtpActivity
import com.tokr.com.ui.widget.ButtonProgress
import com.tokr.com.util.CommonUtil.toast
import com.tokr.com.util.TokrTextWatcher
import kotlinx.android.synthetic.main.activity_login.*
import kotlinx.android.synthetic.main.tokr_custom_widget.view.*

/**
 * <h1>Email Login Activity<h1>
 *
 * <p>This screen is used to login using email and password,
 *
 *    if the user is already registered with application and password is correct
 *    then user will be logged in successfully.
 *
 *    Otherwise a new user will be registered to the application and
 *    will be navigated to the OTP verification screen.
 * </p>
 *
 */


class EmailLoginActivity : BaseActivity(), EmailLoginContract.View, View.OnClickListener {

    private val presenter by lazy {
        EmailLoginPresenter(this)
    }

    companion object {
        private const val EXTRA_FORGOT_PASSWORD: Int = Constants.FORGOT_PASSWORD_CODE
        private const val EXTRA_SUCCESS_MESSAGE: String = Constants.FORGOT_PASSWORD_MESSAGE

        fun createIntent(context: Context) = Intent(context, EmailLoginActivity::class.java)
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        edt_email.edt_tokr_custom.filters = arrayOf<InputFilter>(InputFilter.LengthFilter(EMAIL_MAX_LENGTH))

        inputsTextWatcher()
        tv_forgot_password.setOnClickListener(this)
        tv_back.setOnClickListener(this)

        btn_submit.setButtonListener(object : ButtonProgress.OnButtonClickListener {
            override fun onButtonClick() {
                btn_submit.disableButton()
                hideKeyBoard()
                val request = EmailRequest(edt_email.edt_tokr_custom.text.toString().trim(),
                        edt_password.edt_tokr_custom.text.toString().trim(), getString(R.string.user))
                presenter.login(request)
            }
        })
    }

    private fun inputsTextWatcher() {
        edt_email.edt_tokr_custom.addTextChangedListener(object : TokrTextWatcher() {
            override fun onTextChanged(charSequence: CharSequence, i: Int, i1: Int, i2: Int) {
                presenter.isValidEmail(charSequence.trim().toString())
            }
        })

        edt_password.edt_tokr_custom.addTextChangedListener(object : TokrTextWatcher() {
            override fun onTextChanged(charSequence: CharSequence, i: Int, i1: Int, i2: Int) {
                presenter.isValidPassword(charSequence.toString())
            }
        })
    }

    override val layout: Int
        get() = R.layout.activity_login

    override fun requireDefaultToolbar() = false

    override fun setBottomNavVisibility() = !PrefManager.getInstance().isFirstTimeUser

    override fun showEmailError(msg: Int) {
        edt_email.edt_tokr_custom.error = getString(msg)
    }

    override fun hideEmailError() {
        edt_email.edt_tokr_custom.error = null
    }

    override fun showPasswordError(msg: Int) {
        edt_password.edt_tokr_custom.error = getString(msg)
    }

    override fun hidePasswordError() {
        edt_password.edt_tokr_custom.error = null
    }

    override fun onError() {
        btn_submit.enableButton()
    }

    override fun enableSubmitButton() {
        btn_submit.enableButton()
    }

    override fun disableSubmitButton() {
        btn_submit.disableButton()
    }

    override fun showContentLoading() {
        btn_submit.showLoading()
    }


    override fun hideContentLoading() {
        btn_submit.hideLoading()
    }

    override fun onClick(view: View) {
        when (view.id) {

            R.id.tv_forgot_password -> {
                startActivityForResult(ForgotPasswordActivity.createIntent(this), EXTRA_FORGOT_PASSWORD)
            }
            R.id.tv_back -> {
                hideKeyBoard()
                onBackPressed()
            }
        }
    }

    override fun moveToOtpScreen() {
        startActivity(VerifyOtpActivity.createIntent(this, edt_email.edt_tokr_custom.text.toString(), edt_password.edt_tokr_custom.text.toString()))
        btn_submit.enableButton()
    }

    override
    fun onSuccess(response: LoginBean) {

        val prefManager: PrefManager = PrefManager.getInstance()
        prefManager.saveUserDataToPref(response)
        prefManager.isNewUser = response.isNewUser

        if (prefManager.openSpecificScreen == DISCOVER_SCREEN && !prefManager.isFirstTimeUser) {
            setResult(Activity.RESULT_OK)
            finish()
        } else {
            if (ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED) run {
                startActivity(OnBoardingActivity.createIntent(this))
                finishAffinity()
            } else {
                if (prefManager.isNewUser) {
                    startActivity(OnBoardingActivity.createIntent(this))
                } else {
                    if (prefManager.openSpecificScreen == PROFILE_SCREEN) {
                        startActivity(ProfileActivity.createIntent(this))
                    } else {
                        startActivity(ForYouActivity.createIntent(this))
                    }
                 }
                finishAffinity()
            }
            btn_submit.enableButton()
        }
    }

    override fun onFailure(message: String) {
        btn_submit.enableButton()
        toast(message)
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)

        if (resultCode == Activity.RESULT_OK && requestCode == EXTRA_FORGOT_PASSWORD) {
            if (data != null && data.hasExtra(EXTRA_SUCCESS_MESSAGE)) {
                toast(data.getStringExtra(EXTRA_SUCCESS_MESSAGE))
            }
        }
    }
}