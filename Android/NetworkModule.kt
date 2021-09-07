package com.code.module

import com.facebook.FacebookSdk.getCacheDir
import com.jakewharton.retrofit2.adapter.kotlin.coroutines.CoroutineCallAdapterFactory
import com.code.BuildConfig
import com.code.BuildConfig.API_URL
import com.code.api.SecurityInterceptor
import com.code.api.APIService
import com.code.utils.CommonUtils
import com.code.utils.Constants.CACHE_CONTROL
import com.code.utils.Constants.PUBLIC_MAX_AGE
import com.code.utils.Constants.PUBLIC_ONLY_IF_CACHED
import com.code.utils.Constants.READ_TIMEOUT
import com.code.utils.Constants.WRITE_TIMEOUT
import com.code.utils.Constants.CACHE_CONTROL_LIMIT
import com.code.utils.Constants.CACHE_LIMIT
import okhttp3.Cache
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import org.koin.dsl.module
import retrofit2.CallAdapter
import retrofit2.Retrofit
import retrofit2.adapter.rxjava2.RxJava2CallAdapterFactory
import retrofit2.converter.gson.GsonConverterFactory
import timber.log.Timber
import java.util.concurrent.TimeUnit


/**
 *<h1>NetworkModule</h1>

 *<p>This module contains network related functions and API service creation </p>

 **/
 
const val CAT_API_BASE_URL = API_URL

val networkModule = module {
    // The Retrofit service using our custom HTTP client instance as a singleton
    single {
        createWebService(
            createHttpClient(),
            RxJava2CallAdapterFactory.create(),
            CAT_API_BASE_URL
        )
    }
}

/* Returns a custom OkHttpClient instance with interceptor. Used for building Retrofit service */
fun createHttpClient(): OkHttpClient {
    val cacheSize = Constants.CACHE_SIZE // 10 MB
    val cache = Cache(getCacheDir(), cacheSize.toLong())
    val client = OkHttpClient.Builder()
    client.readTimeout(Constants.READ_TIMEOUT , TimeUnit.MINUTES)
        .writeTimeout(Constants.WRITE_TIMEOUT, TimeUnit.MINUTES)
        .cache(cache)
        .addInterceptor(SecurityInterceptor())

    if (BuildConfig.DEBUG) {
	    // Logging intercepter added to client in case of debug
        val httpLoggingInterceptor = HttpLoggingInterceptor { message -> Timber.d(message) }
        httpLoggingInterceptor.level = HttpLoggingInterceptor.Level.BODY
        client.addInterceptor(httpLoggingInterceptor)
    }

    return client.addInterceptor {
        val original = it.request()
        val requestBuilder = original.newBuilder()
        if (CommonUtils.isNetworkAvailable())
            requestBuilder.header(CACHE_CONTROL, PUBLIC_MAX_AGE + Constants.CACHE_CONTROL_LIMIT).build()
        else
            requestBuilder.header(
                CACHE_CONTROL,
                PUBLIC_ONLY_IF_CACHED + Constants.CACHE_LIMIT
            ).build()

        val request = requestBuilder.method(original.method(), original.body()).build()
        return@addInterceptor it.proceed(request)
    }.build()
}

/* function to build our Retrofit service */
fun createWebService(
    okHttpClient: OkHttpClient,
    factory: CallAdapter.Factory, baseUrl: String
): APIService {
    val retrofit = Retrofit.Builder()
        .baseUrl(baseUrl)
        .addConverterFactory(GsonConverterFactory.create())
        .addCallAdapterFactory(CoroutineCallAdapterFactory())
        .addCallAdapterFactory(factory)
        .client(okHttpClient)
        .build()
    return retrofit.create(APIService::class.java)
}
