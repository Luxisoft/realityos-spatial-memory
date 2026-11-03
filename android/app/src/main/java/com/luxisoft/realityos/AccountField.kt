package com.luxisoft.realityos

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.autofill.ContentType
import androidx.compose.ui.focus.FocusDirection
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.focus.focusRequester
import androidx.compose.ui.focus.onFocusChanged
import androidx.compose.ui.platform.LocalFocusManager
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.contentType
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.input.*
import androidx.compose.ui.unit.dp

@Composable
internal fun AccountField(field: String, value: String, onValue: (String) -> Unit, step: AccountStep, enabled: Boolean, error: Int?, focus: FocusRequester, onBlur: () -> Unit, last: Boolean, onSubmit: () -> Unit) {
    var visible by remember { mutableStateOf(false) }
    var hadFocus by remember { mutableStateOf(false) }
    val focusManager = LocalFocusManager.current
    val password = field == "password"
    val registration = step == AccountStep.Register
    val label = when (field) {
        "name" -> R.string.account_name
        "username" -> R.string.account_username
        "password" -> R.string.local_account_password
        else -> when (step) {
            AccountStep.Login -> R.string.account_identifier
            AccountStep.CorrectEmail -> R.string.account_new_email
            else -> R.string.local_account_email
        }
    }
    val hint = when {
        field == "username" && registration -> R.string.account_username_hint
        password && registration -> R.string.account_password_hint
        else -> null
    }
    val autofillType = when (field) {
        "name" -> ContentType.PersonFullName
        "username" -> if (registration) ContentType.NewUsername else ContentType.Username
        "password" -> if (registration) ContentType.NewPassword else ContentType.Password
        else -> if (step == AccountStep.Login) ContentType.Username + ContentType.EmailAddress else ContentType.EmailAddress
    }
    OutlinedTextField(
        value = value, onValueChange = onValue,
        modifier = Modifier.fillMaxWidth().testTag("account-$field").focusRequester(focus).onFocusChanged {
            if (hadFocus && !it.isFocused) onBlur()
            hadFocus = it.isFocused
        }.semantics { contentType = autofillType },
        enabled = enabled, singleLine = true, isError = error != null,
        textStyle = MaterialTheme.typography.bodyLarge,
        shape = MaterialTheme.shapes.medium,
        label = { Text(stringResource(label), style = MaterialTheme.typography.bodyMedium) },
        leadingIcon = {
            Icon(
                when (field) {
                    "name" -> Icons.Outlined.PersonOutline
                    "username" -> Icons.Outlined.AlternateEmail
                    "password" -> Icons.Outlined.LockOpen
                    else -> Icons.Outlined.MailOutline
                },
                null,
                Modifier.size(22.dp)
            )
        },
        trailingIcon = if (password) {
            (
                {
                    IconButton(onClick = { visible = !visible }, enabled = enabled, modifier = Modifier.testTag("account-password-visibility")) {
                        Icon(
                            if (visible) Icons.Outlined.VisibilityOff else Icons.Outlined.Visibility,
                            stringResource(if (visible) R.string.account_hide_password else R.string.account_show_password),
                            Modifier.size(22.dp)
                        )
                    }
                }
                )
        } else {
            null
        },
        supportingText = if (error != null || hint != null) ({ Text(stringResource(error ?: hint!!), modifier = Modifier.testTag("account-$field-help")) }) else null,
        visualTransformation = if (password && !visible) PasswordVisualTransformation() else VisualTransformation.None,
        keyboardOptions = KeyboardOptions(
            keyboardType = if (password) {
                KeyboardType.Password
            } else if (field == "email" && step != AccountStep.Login) {
                KeyboardType.Email
            } else {
                KeyboardType.Text
            },
            capitalization = if (field == "name") KeyboardCapitalization.Words else KeyboardCapitalization.None,
            autoCorrectEnabled = field == "name",
            imeAction = if (last) ImeAction.Done else ImeAction.Next
        ),
        keyboardActions = KeyboardActions(onNext = { focusManager.moveFocus(FocusDirection.Next) }, onDone = { onSubmit() }),
        colors = OutlinedTextFieldDefaults.colors(
            focusedContainerColor = AccountFieldSurface, unfocusedContainerColor = AccountFieldSurface,
            disabledContainerColor = AccountFieldSurface, errorContainerColor = AccountFieldSurface,
            unfocusedBorderColor = MaterialTheme.colorScheme.outlineVariant,
            unfocusedLabelColor = AccountMuted, unfocusedLeadingIconColor = AccountMuted,
            focusedLeadingIconColor = AccountBlue, focusedLabelColor = AccountBlue,
            unfocusedTrailingIconColor = AccountMuted, focusedTrailingIconColor = AccountBlue,
            unfocusedSupportingTextColor = AccountMuted
        )
    )
}
