function addGlobalCheckbox(element) {
    var checkOnlyRegister = false;

    if (element.find('.register-form.state-form').length > 0) {
        element = element.find('.register-form.state-form');
        checkOnlyRegister = true;
    }

    if (element.find('.login-form.state-form').length > 0 && !checkOnlyRegister) {
        return function (params) {
            return true;
        };
    }

    if (element.find('.form-content').length > 0) {
        element = element.find('.form-content');
    }

    function hasFormPaidOrder() {
        var formPositionSum = 0;

        element.find(".form-position-input, input[name='formParams[setted_offer_id]'], input.offer-select-input").each(
            function () {
                formPositionSum += $(this).data("price-value");
            }
        );

        if (formPositionSum > 0) {
            return true;
        }

        if (element.parent("form").find('input[name="formParams[willCreatePaidDeal]"]').val() > 0) {
            return true;
        }

        return false;
    }

    var isOfertaCheckboxEnabled = window.globalCheckboxEnabled;

    if (window.hasOwnProperty("globalCheckboxForPaidOnly")) {
        if (window.globalCheckboxForPaidOnly && !hasFormPaidOrder()) {
            isOfertaCheckboxEnabled = false;
        }
    }

    if (isOfertaCheckboxEnabled) {
        var checked = window.persodataConfirm ? 'checked' : '';
        var $checkboxEl = $('<div class="global-confirm-checkbox-block confirm-rules-checkbox">' +
            '<label>' +
            '<input class="global-confirm-checkbox" type="checkbox" ' + checked + ' name="globalConfirmCheckbox" >' +
            '<span class="checkbox-text">' + window.globalCheckboxText + '</span>' +
            '</label>' +
            '</div>');

        var $checkboxInput = $checkboxEl.find('input')
        var firstSubmitButton = element.find('button[type=submit]');
        // if (firstSubmitButton.length > 0 && false) {
        //     $checkboxEl.insertBefore(firstSubmitButton)
        // } else {
            $checkboxEl.appendTo(element);
        // }
    }

    if (window.pdpCheckboxEnabled) {
        var isPdpChecked = window.pdpConfirmedByDefault ? 'checked' : '';
        var $pdpCheckboxEl = $('<div class="global-confirm-checkbox-block confirm-rules-checkbox">' +
            '<label>' +
            '<input class="global-confirm-checkbox" type="checkbox" ' + isPdpChecked + ' name="pdpConfirmCheckbox" >' +
            '<span class="checkbox-text">' + window.pdpCheckboxText + '</span>' +
            '</label>' +
            '</div>');

        var $pdpCheckboxInput = $pdpCheckboxEl.find('input')

        $pdpCheckboxEl.appendTo(element);
    }

    var isMailingCheckboxEnabled = window.checkboxMailingEnabled;
    if (window.hasOwnProperty("checkboxMailingForPaidOnly")) {
        if (window.checkboxMailingForPaidOnly && !hasFormPaidOrder()) {
            isMailingCheckboxEnabled = false;
        }
    }

    if (isMailingCheckboxEnabled) {
        var checked = window.checkboxMailingChecked ? 'checked' : '';
        var input = '<div class="xdget-formField">' +
            '<label>' +
            '<input type="checkbox" ' + checked + ' class="append-handle-input" name="confirmMailingCheckbox" />' +
            '<span class="checkbox-text">' + window.checkboxMailingText + '</span>' +
            '</label>' +
            '</div>';

        var checkboxMailing = $(input);

        if (element.find('.confirm-rules-checkbox').length === 1) {
            checkboxMailing.appendTo(element.find('.confirm-rules-checkbox'));
        } else {
            checkboxMailing = $('<div class="global-confirm-checkbox-block confirm-mailing-checkbox">' + input + '</div>');

            var firstSubmitButton = element.find('button[type=submit]');
            checkboxMailing.appendTo(element);
        }
    }

    return function (params) {
        var str = "";
        if (isOfertaCheckboxEnabled && !$checkboxInput.prop('checked')) {
            if (checkOnlyRegister && !(params && params.state == "register")) {
                return true;
            }

            str = 'Чтобы отправить форму вы должны согласиться с условиями договора-оферты. '
                + 'Отметьте соответствующую галочку';

            if (window.hasOwnProperty("isLegalReworkFeatureEnabled")) {
                if (window.isLegalReworkFeatureEnabled === true) {
                    str = "Чтобы продолжить, необходимо согласиться с условиями оферты";
                }
            }

            if (typeof Yii != 'undefined') {
                str = Yii.t('common', str);
            }

            alert(str);

            return false;
        }

        if (window.pdpCheckboxEnabled && !$pdpCheckboxInput.prop('checked')) {
            if (checkOnlyRegister && !(params && params.state == "register")) {
                return true;
            }

            str = 'Чтобы отправить форму вы должны согласиться с условиями на обработку персональных данных. '
                + 'Отметьте соответствующую галочку';

            if (window.hasOwnProperty("isLegalReworkFeatureEnabled")) {
                if (window.isLegalReworkFeatureEnabled === true) {
                    str = "Чтобы продолжить, необходимо согласиться с условиями обработки персональных данных";
                }
            }

            if (typeof Yii != 'undefined') {
                str = Yii.t('common', str);
            }

            alert(str);

            return false;
        }

        if (isMailingCheckboxEnabled) {
            var isRequired = false;
            if (window.hasOwnProperty("isMailingCheckboxRequired")) {
                if (window.isMailingCheckboxRequired) {
                    isRequired = true;
                }
            }

            if (window.hasOwnProperty("isMailingCheckboxRequiredForNotPaid")) {
                if (window.isMailingCheckboxRequiredForNotPaid && !hasFormPaidOrder()) {
                    isRequired = true;
                }
            }

            if (isRequired) {
                if (!checkboxMailing.find("input").prop("checked")) {
                    if (checkOnlyRegister && !(params && params.state == "register")) {
                        return true;
                    }

                    str = "Для того, чтобы мы могли отправлять вам сообщения на почту, "
                        + "необходимо согласиться на получение писем";

                    if (typeof Yii != 'undefined') {
                        str = Yii.t('common', str);
                    }

                    alert(str);

                    return false;
                }
            }
        }

        return true;
    };
}
