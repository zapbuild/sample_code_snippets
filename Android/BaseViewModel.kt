package com.code.base

import android.os.Build
import androidx.annotation.RequiresApi
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import com.code.data.model.Error
import com.code.data.model.GenericResponse
import com.code.utils.CommonUtils
import com.code.utils.UseCaseResult
import kotlinx.coroutines.CoroutineExceptionHandler
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import timber.log.Timber
import kotlin.coroutines.CoroutineContext

/**
 *<h1>BaseViewModel</h1>

 *<p>This class is used to handle API's responses, exceptions and errors </p>

 **/

open class BaseViewModel() : ViewModel(), CoroutineScope {

    private val job = Job()

    val errorMessage = MutableLiveData<String>()
    var errorArray = MutableLiveData<List<Error>>()
    val retry = MutableLiveData<() -> Unit>()

    override val coroutineContext: CoroutineContext

        get() = job + Dispatchers.Main

    override fun onCleared() {
        super.onCleared()
        job.cancel()
    }

    fun isValidNetwork(retryInterface: () -> Unit): Boolean {
        val isAvailable = CommonUtils.isNetworkAvailable()
        if (!isAvailable) {
            retry.value = retryInterface
        }
        return isAvailable
    }

    fun <T : Any> apiSuccess(
        state: MutableLiveData<GenericResponse<T>>,
        result: UseCaseResult<GenericResponse<T>>
    ) {
        when (result) {
            is UseCaseResult.Success -> {
                if (result.data.status?.code == Constants.SUCCESS) {
                    state.value = result.data
                } else if (result.data.status?.code != null && result.data.status?.code >= Constants.CODE_BAD_REQUEST) {
                    if (result.data.status?.errors != null && result.data.status?.errors?.isEmpty()) {
                        errorMessage.value = result.data.status?.message
                    } else
                        errorArray.value = result.data.status?.errors
                }
            }
            is UseCaseResult.Exception -> errorMessage.value = result.exception.message
        }
    }

}

