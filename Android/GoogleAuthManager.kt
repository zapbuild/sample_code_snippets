package com.code.utils.manager.google

import android.annotation.SuppressLint
import android.os.Bundle
import androidx.fragment.app.FragmentActivity
import com.google.android.gms.auth.api.Auth
import com.google.android.gms.auth.api.signin.GoogleSignInOptions
import com.google.android.gms.auth.api.signin.GoogleSignInResult
import com.google.android.gms.common.ConnectionResult
import com.google.android.gms.common.Scopes
import com.google.android.gms.common.api.GoogleApiClient
import com.google.android.gms.common.api.Scope
import com.code.R
import com.code.base.BaseActivity
import com.code.data.model.SignUpRequest
import com.code.utils.Constants
import com.code.utils.Constants.PROVIDER_GOOGLE
import okhttp3.*
import org.json.JSONException
import org.json.JSONObject
import timber.log.Timber
import java.io.IOException
import java.util.*

/**
 * <h>Google Signin Helper</h>
 *
 * <p>This class is handling google sign in success,failure</p>
 *
 */

class GoogleAuthManager(private val activity: BaseActivity) :
    GoogleApiClient.OnConnectionFailedListener, GoogleApiClient.ConnectionCallbacks {
	
    private var listener: GoogleAuthListener? = null
    private var googleApiClient: GoogleApiClient? = null

    /**
     * return the googleApiClient and Build if null
     */
    private fun getGoogleApiClient(): GoogleApiClient {
        if (googleApiClient == null) {
            val gso = GoogleSignInOptions.Builder(GoogleSignInOptions.DEFAULT_SIGN_IN)
                .requestServerAuthCode(activity.getString(R.string.google_client_id))
                .requestEmail()
                .requestProfile()
                .requestScopes(Scope(Scopes.DRIVE_APPFOLDER))
                .build()

            googleApiClient =
                GoogleApiClient.Builder(activity)
                    .enableAutoManage(activity, 1, this)
                    .addOnConnectionFailedListener(this)
                    .addConnectionCallbacks(this)
                    .addApi(Auth.GOOGLE_SIGN_IN_API, gso)
                    .addScope(Scope(Constants.EMAIL))
                    .build()
        }
        return googleApiClient!!
    }

    fun setListener(listener: GoogleAuthListener): GoogleAuthManager {
        this.listener = listener
        return this
    }

    fun login() {
        if (getGoogleApiClient().isConnected) {
            signIn()
        } else {
            getGoogleApiClient().connect()
        }
    }

    override fun onConnected(bundle: Bundle?) {
        signIn()
    }

/* method to handle result of signin */
    fun handleSignInResult(result: GoogleSignInResult) {
        if (result.isSuccess) {
            val acct = result.signInAccount
            val client = OkHttpClient()
            assert(acct != null)
            val requestBody = FormBody.Builder()
                .add(Constants.GRANT_TYPE, activity.getString(R.string.authorization_code))
                .add(Constants.CLIENT_ID, activity.getString(R.string.google_client_id))
                .add(Constants.CLIENT_SECRET, activity.getString(R.string.google_client_secret))
                .add(Constants.REDIRECT_URL, "")
                .add(Constants.CODE, acct?.serverAuthCode!!)
                .build()
            val request = Request.Builder()
                .url(OAUTH_TOKEN_URL)
                .post(requestBody)
                .build()
            client.newCall(request).enqueue(object : Callback {
                override fun onFailure(call: Call, e: IOException) {
                    Timber.d("loginUsingGoogleSignIn onFailure =%s", e.toString())
                }

                @Throws(IOException::class)
                override fun onResponse(call: Call, response: Response) {
                    try {
                        assert(response.body() != null)
                        val jsonObject = JSONObject(response.body()?.string())
                        signOut()
                        val accessToken = jsonObject.getString(Constants.ACCESS_TOKEN)
                        val id = acct.id!!
                        val signUpRequest = SignUpRequest()
                        signUpRequest.email = acct.email
                        val arrayName = acct.displayName?.split(" ")
                        signUpRequest.firstName = arrayName?.get(0)
                        if (arrayName?.size!! >= 1)
                            signUpRequest.lastName = arrayName.get(1)
                        signUpRequest.providerId = acct.id
                        signUpRequest.providerName = PROVIDER_GOOGLE
                        listener?.success(signUpRequest)
                    } catch (e: JSONException) {
                        e.printStackTrace()
                    }
                }
            })
        } else {
            Timber.d(activity.getString(R.string.something_went_wrong))
        }
    }

    override fun onConnectionSuspended(i: Int) {
        Timber.d(activity.getString(R.string.something_went_wrong))
    }

    override fun onConnectionFailed(connectionResult: ConnectionResult) {
        Timber.d(activity.getString(R.string.something_went_wrong))
    }

    private fun signIn() {
        signOut()
        val signInIntent = Auth.GoogleSignInApi.getSignInIntent(getGoogleApiClient())
        activity.startActivityForResult(signInIntent, GOOGLE_SIGN_IN)
    }

    private fun signOut() {
        if (googleApiClient != null && googleApiClient?.isConnected)
            Auth.GoogleSignInApi.signOut(getGoogleApiClient()).setResultCallback { }
    }

    /**
     * disconnect google API client when needed
     */
    @SuppressLint("NewApi")
    fun disconnect() {
        if (getGoogleApiClient().isConnected) {
            signOut()
            getGoogleApiClient().disconnect()
        }
        getGoogleApiClient().stopAutoManage(Objects.requireNonNull<FragmentActivity>(activity))
        googleApiClient = null
    }

    companion object {

        const val GOOGLE_SIGN_IN = 9001
        private const val OAUTH_TOKEN_URL = "https://www.googleapis.com/oauth2/v4/token"
    }
}



