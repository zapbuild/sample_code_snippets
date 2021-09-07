package com.code.api

import com.code.data.local.PrefManager
import okhttp3.Interceptor
import okhttp3.Response
import java.io.IOException

/**
 *<h1>SecurityInterceptor</h1>

 *<p>Interceptor for adding headers to the API </p>

 **/
class SecurityInterceptor : Interceptor {

    @Throws(IOException::class)
    override fun intercept(chain: Interceptor.Chain): Response {
        val request = chain.request().newBuilder()

        request.header(Constants.USER_AGENT, Constants.USER_ANDROID)
		// To check whether user is logged in or not
        if (PrefManager.isUserLoggedIn())
            request.addHeader(Constants.HEADER_AUTHORIZATION, PrefManager.getUserPref()?.token!!)

        return chain.proceed(request.build())

    }
}