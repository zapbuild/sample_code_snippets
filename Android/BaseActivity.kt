package com.code.base

import android.app.Activity
import android.content.Intent
import android.content.IntentFilter
import android.content.SharedPreferences
import android.os.Bundle
import android.os.Handler
import android.view.LayoutInflater
import android.view.View.GONE
import android.view.View.VISIBLE
import androidx.annotation.LayoutRes
import androidx.annotation.NonNull
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.databinding.DataBindingUtil
import androidx.databinding.ViewDataBinding
import com.google.android.gms.auth.api.Auth
import com.google.android.libraries.places.api.Places
import com.google.android.material.snackbar.Snackbar
import com.code.R
import com.code.databinding.ContentMainBinding
import com.code.utils.CommonUtils.*
import com.code.utils.DialogListener
import com.code.utils.manager.facebook.FacebookListener
import com.code.utils.manager.facebook.FacebookManager
import com.code.utils.manager.google.GoogleAuthListener
import com.code.utils.manager.google.GoogleAuthManager
import com.code.utils.manager.google.GoogleAuthManager.Companion.GOOGLE_SIGN_IN
import kotlinx.android.synthetic.main.container_layout.*
import kotlinx.android.synthetic.main.toolbar.*
import timber.log.Timber


abstract class BaseActivity : AppCompatActivity(), BaseView {

    var baseBinding: ContentMainBinding? = null

    private lateinit var alertDialog: AlertDialog
    private var googleManager: GoogleAuthManager? = null
    private var facebookManager: FacebookManager? = null
  
    /**
     * Need to implement this method if we are using data binding in UI
     */
    protected open fun <T : ViewDataBinding> getLayout(@LayoutRes resId: Int): T {
        return DataBindingUtil.inflate(layoutInflater, resId, baseBinding?.containers, true)
    }

    /**
     * Need to implement this method if we are not using data binding in UI
     */
    @LayoutRes
    protected open fun getLayout(): Int = 0

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        //initialize places api
        Places.initialize(applicationContext, getString(R.string.google_places_api_key))

        if (getLayout() != 0) {
            if (!hasNavDrawer()) {
                setContentView(R.layout.content_main)
            } else {
                setContentView(R.layout.activity_nav_drawer)
            }

            val view = LayoutInflater.from(this).inflate(getLayout(), null, false)
            container.addView(view, 0)
        } else {
            if (!hasNavDrawer())
                baseBinding = DataBindingUtil.setContentView(this, R.layout.content_main)
            else
                baseBinding = DataBindingUtil.setContentView(this, R.layout.activity_nav_drawer)
        }

        registerReceiver(
            networkChangeReceiver,
            IntentFilter("android.net.conn.CONNECTIVITY_CHANGE")
        )
        handleToolbar()
    }

    protected open fun hasNavDrawer(): Boolean {
        return false
    }


    private fun handleToolbar() {
        if (hasOptionMenus()) {
            setSupportActionBar(toolbar)
        }
        if (hasToolbar()) {
            supportActionBar?.setDisplayShowTitleEnabled(true)
            if (!hasNavDrawer()) {
                toolbar.setNavigationIcon(R.drawable.ic_back_icon)
                toolbar.setNavigationOnClickListener {
                    onBackPressed()
                }
            }
            toolbar.visibility = VISIBLE
            toolbar.title = setToolbarText()
        } else {
            toolbar.visibility = GONE
        }

    }

    protected open fun hasToolbar(): Boolean = false
    protected open fun hasOptionMenus(): Boolean = false
    protected open fun setToolbarText(): String = ""

    /**
     * show dialog
     *
     * @param title   title to show(Alert)
     * @param message error message
     * @param retry   callback
     */
    fun showDialog(title: String, message: String) {

        val builder = AlertDialog.Builder(
            this
        )
        builder.setTitle(title)
            .setMessage(message)
            .setCancelable(false)
            .setPositiveButton(getString(R.string.ok), null)

        alertDialog = builder.create()
        if (!this.isFinishing) {
            if (!alertDialog.isShowing)
                alertDialog.show()
        }
    }

    /**
     * show retry dialog
     *
     * @param title   title to show(Alert)
     * @param message message of error(No Internet connection! Please check your data or wifi connection and try again)
     * @param retry   callback
     */
    private fun showRetryDialog(title: String, message: String, retry: () -> Unit) {
        val builder = AlertDialog.Builder(
            this
        )
        builder.setTitle(title)
            .setMessage(message)
            .setCancelable(false)
            .setPositiveButton(getString(R.string.retry)) { _, _ -> run(retry) }
            .setNegativeButton(getString(R.string.back)) { _, _ -> onBackPressed() }

        alertDialog = builder.create()
        if (!this.isFinishing) {
            if (!alertDialog.isShowing)
                alertDialog.show()
        }
    }

    fun showSnackBar(message: String) {
        val snackBar: Snackbar =
            Snackbar.make(container, message, Snackbar.LENGTH_SHORT)
        snackBar.show()
    }

    override fun showError(error: String) {
        hideLoading()
        showDialog(getString(R.string.alert), error)
    }

    override fun showError(message: String, retry: () -> Unit) {
        hideLoading()
        showRetryDialog(getString(R.string.alert), message, retry)
    }

    override fun showLoading() {
        if (CommonUtils.isNetworkAvailable()) {
            progressBar.visibility = VISIBLE
        }
    }

    override fun hideLoading() {
        progressBar.visibility = GONE
    }

    override fun showNoInternetError(retry: () -> Unit) {
        hideLoading()
        showRetryDialog(
            getString(R.string.alert),
            resources.getString(R.string.error_internet),
            retry
        )
    }

    override fun showToast(message: String?) {
        message?.let {
            CommonUtils.toast(it)
        }
    }

    override fun showToast(message: Int?) {
        message?.let {
            CommonUtils.toast(it.toString())
        }
    }

    override fun showAlertDialog(
        message: String,
        positiveText: String,
        negativeText: String,
        alertListener: DialogListener
    ) {
        hideLoading()
        val builder = AlertDialog.Builder(this)
        builder.setMessage(message).setCancelable(false)
            .setPositiveButton(positiveText) { _, _ -> alertListener.onOkClicked() }
            .setNegativeButton(negativeText) { _, _ -> alertDialog.dismiss() }
        showBuild(builder)
    }

    /**
     * create alert dialog from builder
     */
    private fun showBuild(@NonNull builder: AlertDialog.Builder) {
        alertDialog = builder.create()
        if (!this.isFinishing) {
            if (!alertDialog.isShowing)
                alertDialog.show()
        }
    }

    override fun baseApplication(): BaseApp {
        return application as BaseApp
    }

    protected fun googleSignIn(listener: GoogleAuthListener) {
        getGoogleManager().setListener(listener).login()
    }

    protected fun facebookSignIn(listener: FacebookListener) {
        getFacebookManager().setListener(listener).login()
    }

    private fun getGoogleManager(): GoogleAuthManager {
        if (googleManager == null) {
            googleManager = GoogleAuthManager(this)
        }
        return googleManager!!
    }

    private fun getFacebookManager(): FacebookManager {
        if (facebookManager == null) {
            facebookManager = FacebookManager(this)
        }
        return facebookManager!!
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        if (resultCode == Activity.RESULT_OK) {
            getFacebookManager().getcallBackManager()
                ?.onActivityResult(requestCode, resultCode, data)
            when (requestCode) {
                GOOGLE_SIGN_IN -> {
                    val result = Auth.GoogleSignInApi.getSignInResultFromIntent(data)
                    googleManager?.handleSignInResult(result)
                }
                else -> {
                    super.onActivityResult(requestCode, resultCode, data)
                }
            }
        } else {
            googleManager?.disconnect()
        }
    }

    override fun showFullScreenLoader() {
        full_screen_loader.visibility = VISIBLE
    }

    override fun hideFullScreenLoader() {
        full_screen_loader.visibility = GONE
    }

}