package com.luxisoft.realityos

import android.Manifest
import android.annotation.SuppressLint
import android.content.pm.PackageManager
import android.graphics.BitmapFactory
import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import androidx.core.content.FileProvider
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.io.ByteArrayOutputStream
import java.io.File
import java.net.HttpURLConnection
import java.net.URL

/** Mandatory private face capture plus silent identity verification against Facebook faces. */
@Composable
@SuppressLint("LocalContextGetResourceValueCall")
internal fun FaceCaptureScreen(
    hasCapture: Boolean,
    onDone: () -> Unit,
    onDenied: (String) -> Unit,
    allowPhoto: Boolean = true,
    onRequireLogin: () -> Unit = {}
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    var preview by remember { mutableStateOf<android.graphics.Bitmap?>(null) }
    var busy by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf("") }
    var needsPhoto by remember { mutableStateOf(!hasCapture) }
    var pending by remember { mutableStateOf(false) }
    var attemptsLeft by remember { mutableStateOf<Int?>(null) }
    var lockedSeconds by remember { mutableStateOf<Int?>(null) }

    fun verify() {
        scope.launch {
            busy = true
            error = ""
            pending = false
            lockedSeconds = null
            try {
                val (code, body) = withContext(Dispatchers.IO) {
                    val connection = URL("${BuildConfig.DEFAULT_REALITYOS_API_BASE_URL}/faces/verify-identity").openConnection() as HttpURLConnection
                    connection.requestMethod = "POST"
                    connection.connectTimeout = 15000
                    connection.readTimeout = 60000
                    SocialSession.token?.let { connection.setRequestProperty("Authorization", "Bearer $it") }
                    try {
                        val statusCode = connection.responseCode
                        val stream = if (statusCode in 200..299) connection.inputStream else connection.errorStream
                        statusCode to (stream?.bufferedReader()?.use { it.readText() }.orEmpty())
                    } finally { connection.disconnect() }
                }
                when (code) {
                    200 -> {
                        val result = JSONObject(body)
                        if (result.optBoolean("verified")) onDone()
                        else when (result.optString("status")) {
                            "pending" -> pending = true
                            "locked" -> {
                                lockedSeconds = result.optInt("retry_after_seconds", 1800)
                                needsPhoto = false
                            }
                            else -> {
                                attemptsLeft = if (result.isNull("attempts_remaining")) null
                                else result.optInt("attempts_remaining")
                                needsPhoto = true
                            }
                        }
                    }
                    401 -> onRequireLogin()
                    403 -> onDenied(context.getString(R.string.face_verify_failed))
                    409 -> needsPhoto = true
                    else -> error = context.getString(R.string.face_verify_failed)
                }
            } catch (e: Exception) { error = context.getString(R.string.face_verify_failed) }
            finally { busy = false }
        }
    }

    fun upload(bytes: ByteArray) {
        scope.launch {
            busy = true
            error = ""
            var enrolled = false
            try {
                val result = withContext(Dispatchers.IO) {
                    JSONObject(SocialSession.requestMultipart("faces/profile-photo", emptyMap(), bytes, "face-capture.jpg", "image/jpeg"))
                }
                if (result.optInt("faces_enrolled") < 1) error = context.getString(R.string.face_capture_empty)
                else enrolled = true
            } catch (e: Exception) {
                if (SocialSession.token == null) onRequireLogin()
                else error = e.message.orEmpty()
            }
            finally { if (!enrolled) busy = false }
            if (enrolled) {
                needsPhoto = false
                verify()
            }
        }
    }

    LaunchedEffect(hasCapture) {
        // Always check: verifies a stored capture, or surfaces lockout even
        // when no capture exists yet (409 simply opens the photo UI).
        verify()
    }

    var captureUri by remember { mutableStateOf<Uri?>(null) }

    fun downscaleToLimit(raw: ByteArray, maxSide: Int = 1600): Pair<ByteArray, android.graphics.Bitmap?> {
        val orientation = try {
            android.media.ExifInterface(java.io.ByteArrayInputStream(raw)).getAttributeInt(
                android.media.ExifInterface.TAG_ORIENTATION, android.media.ExifInterface.ORIENTATION_NORMAL)
        } catch (e: Exception) { android.media.ExifInterface.ORIENTATION_NORMAL }
        val bounds = BitmapFactory.Options().apply { inJustDecodeBounds = true }
        BitmapFactory.decodeByteArray(raw, 0, raw.size, bounds)
        var sample = 1
        while ((bounds.outWidth / sample) > maxSide || (bounds.outHeight / sample) > maxSide) sample *= 2
        val decoded = BitmapFactory.decodeByteArray(raw, 0, raw.size, BitmapFactory.Options().apply { inSampleSize = sample })
            ?: return raw to null
        val scaled = if (decoded.width > maxSide || decoded.height > maxSide) {
            val factor = maxSide.toFloat() / maxOf(decoded.width, decoded.height)
            android.graphics.Bitmap.createScaledBitmap(decoded, (decoded.width * factor).toInt(), (decoded.height * factor).toInt(), true)
        } else decoded
        val matrix = android.graphics.Matrix()
        when (orientation) {
            android.media.ExifInterface.ORIENTATION_ROTATE_90 -> matrix.postRotate(90f)
            android.media.ExifInterface.ORIENTATION_ROTATE_180 -> matrix.postRotate(180f)
            android.media.ExifInterface.ORIENTATION_ROTATE_270 -> matrix.postRotate(270f)
            android.media.ExifInterface.ORIENTATION_FLIP_HORIZONTAL -> matrix.postScale(-1f, 1f)
            android.media.ExifInterface.ORIENTATION_FLIP_VERTICAL -> matrix.postScale(1f, -1f)
            android.media.ExifInterface.ORIENTATION_TRANSPOSE -> { matrix.postRotate(90f); matrix.postScale(-1f, 1f) }
            android.media.ExifInterface.ORIENTATION_TRANSVERSE -> { matrix.postRotate(270f); matrix.postScale(-1f, 1f) }
        }
        val upright = if (matrix.isIdentity) scaled
        else android.graphics.Bitmap.createBitmap(scaled, 0, 0, scaled.width, scaled.height, matrix, true)
        val stream = ByteArrayOutputStream()
        upright.compress(android.graphics.Bitmap.CompressFormat.JPEG, 90, stream)
        return stream.toByteArray() to upright
    }

    val takePicture = rememberLauncherForActivityResult(ActivityResultContracts.TakePicture()) { success ->
        val uri = captureUri
        if (!success || uri == null) return@rememberLauncherForActivityResult
        scope.launch {
            error = ""
            try {
                val raw = withContext(Dispatchers.IO) { context.contentResolver.openInputStream(uri)?.use { it.readBytes() } }
                if (raw == null) {
                    error = context.getString(R.string.face_unreadable)
                } else {
                    val (bytes, bitmap) = downscaleToLimit(raw)
                    preview = bitmap
                    upload(bytes)
                }
            } catch (e: Exception) { error = e.message.orEmpty() }
        }
    }

    fun launchCamera() {
        val dir = File(context.cacheDir, "captures").apply { mkdirs() }
        val file = File(dir, "face-capture.jpg")
        if (file.exists()) file.delete()
        val uri = FileProvider.getUriForFile(context, "${context.packageName}.fileprovider", file)
        captureUri = uri
        takePicture.launch(uri)
    }
    val pickImage = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri ->
        if (uri == null) return@rememberLauncherForActivityResult
        scope.launch {
            val raw = try {
                withContext(Dispatchers.IO) { context.contentResolver.openInputStream(uri)?.use { it.readBytes() } }
            } catch (e: Exception) { null }
            if (raw == null) {
                error = context.getString(R.string.face_unreadable)
            } else {
                val (bytes, bitmap) = downscaleToLimit(raw)
                preview = bitmap
                upload(bytes)
            }
        }
    }
    val askCamera = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        if (granted) launchCamera() else error = context.getString(R.string.face_capture_no_camera)
    }

    Surface(Modifier.fillMaxSize(), color = MaterialTheme.colorScheme.background) {
        Column(Modifier.fillMaxSize().safeDrawingPadding().padding(horizontal = 24.dp, vertical = 14.dp),
            horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.Center) {
            Icon(Icons.Default.Face, null, Modifier.size(64.dp), tint = MaterialTheme.colorScheme.tertiary)
            Spacer(Modifier.height(12.dp))
            Text(stringResource(R.string.face_capture_title), style = MaterialTheme.typography.titleLarge)
            Spacer(Modifier.height(8.dp))
            Text(stringResource(R.string.face_capture_body), style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant)
            Spacer(Modifier.height(16.dp))
            if (needsPhoto && !allowPhoto) {
                LaunchedEffect(Unit) { onRequireLogin() }
                CircularProgressIndicator(Modifier.size(32.dp))
            } else if (needsPhoto) {
                if (attemptsLeft != null) {
                    Text(stringResource(R.string.face_verify_failed), color = MaterialTheme.colorScheme.error,
                        style = MaterialTheme.typography.bodyMedium)
                    Spacer(Modifier.height(8.dp))
                    Text(stringResource(R.string.face_attempts_left, attemptsLeft ?: 0),
                        color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodyMedium)
                    Spacer(Modifier.height(16.dp))
                }
                if (preview != null) {
                    Image(preview!!.asImageBitmap(), null, contentScale = ContentScale.Crop,
                        modifier = Modifier.size(160.dp).clip(CircleShape))
                    Spacer(Modifier.height(16.dp))
                }
                if (busy) {
                    CircularProgressIndicator(Modifier.size(32.dp))
                    Spacer(Modifier.height(16.dp))
                }
                if (error.isNotBlank()) {
                    Text(error, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodyMedium)
                    Spacer(Modifier.height(16.dp))
                }
                Button(onClick = {
                    if (ContextCompat.checkSelfPermission(context, Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED) launchCamera()
                    else askCamera.launch(Manifest.permission.CAMERA)
                }, enabled = !busy, modifier = Modifier.fillMaxWidth().widthIn(max = 560.dp).heightIn(min = 56.dp)) {
                    Text(stringResource(R.string.face_capture_take))
                }
                Spacer(Modifier.height(8.dp))
                TextButton(onClick = { pickImage.launch("image/*") }, enabled = !busy) {
                    Text(stringResource(R.string.face_capture_pick))
                }
            } else {
                if (busy) {
                    CircularProgressIndicator(Modifier.size(32.dp))
                    Spacer(Modifier.height(12.dp))
                    Text(stringResource(R.string.face_verifying), style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant)
                } else if (lockedSeconds != null) {
                    Icon(Icons.Default.Lock, null, Modifier.size(48.dp), tint = MaterialTheme.colorScheme.error)
                    Spacer(Modifier.height(12.dp))
                    Text(stringResource(R.string.face_locked_title), style = MaterialTheme.typography.titleMedium,
                        color = MaterialTheme.colorScheme.error)
                    Spacer(Modifier.height(8.dp))
                    Text(stringResource(R.string.face_locked_body, ((lockedSeconds ?: 0) + 59) / 60),
                        style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    Spacer(Modifier.height(12.dp))
                    Button(onClick = { verify() }) { Text(stringResource(R.string.face_retry)) }
                } else if (pending) {
                    Text(stringResource(R.string.face_verify_pending), style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant)
                    Spacer(Modifier.height(12.dp))
                    Button(onClick = { verify() }) { Text(stringResource(R.string.face_retry)) }
                } else if (error.isNotBlank()) {
                    Text(error, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodyMedium)
                    Spacer(Modifier.height(12.dp))
                    Button(onClick = { verify() }) { Text(stringResource(R.string.face_retry)) }
                }
            }
        }
    }
}
