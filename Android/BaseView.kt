package com.code.base

import androidx.annotation.StringRes
import com.code.utils.DialogListener

/**
 *<h1>BaseView.kt</h1>

 *<p>This file contains all the common methods/p>

 **/
 
interface BaseView {

    fun baseApplication(): BaseApp
    fun showError(error: String)
    fun showError(message: String, retry: () -> Unit)
    fun showLoading()
    fun hideLoading()
    fun showNoInternetError(retry: () -> Unit)
    fun showToast(message: String?)
    fun showToast(@StringRes message: Int?)

    fun showAlertDialog(
        message: String,
        positiveText: String,
        negativeText: String,
        alertListener: DialogListener
    )

    fun showFullScreenLoader()

    fun hideFullScreenLoader()

}