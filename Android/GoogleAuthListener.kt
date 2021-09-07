package com.code.utils.manager.google

import com.code.data.model.SignUpRequest


/**
 *<h1>GoogleAuthListener</h1>

 *<p>This class contains methods for google success and failures</p>

 **/

interface GoogleAuthListener {

    fun success(socialRequest: SignUpRequest)
    fun failure()

}
