// Shard key checks.
function containsInvalidShardKeyCharacters(value) {
    if (value === '') {
        return true;
    }

    var unpermitted_char_regex = /[\/\\\"\*\<\>\:\|\?\{\}\,\s]/;
    result = unpermitted_char_regex.test(value);

    return result;
}

function addNewShardKey() {
    var shardKey = $('#shardkeys').val();


    if (shardKey) {
        if (shardKey === '') {
            return false;
        }

        if (containsInvalidShardKeyCharacters(shardKey)){
            var validator = $('#shardKeyForm').validate();
            validator.showErrors({"shardkeys": 'Cannot contain /\ ",*<>:|?{}'});
            return false;
        }

        var shardKeys = $('#shard_key_div').data('keys');

        if (!shardKeys) {
            // $('#shard_key_div').append("<br>");
            $('#shard_key_label').append("<label><b>Selected Shard Keys:</b></label>");
            shardKeys = [];
        }

        if (shardKeys.indexOf(shardKey) == -1) {
            var keyIsHashed = false;

            if ($('#key_is_hashed').is(':checked')) {
                keyIsHashed = true;
            }

            shardKeys.push(shardKey);
            $('#shard_key_div').data('keys', shardKeys);

            var shardKeyLabel = '<label>' + $('#shardkeys').val();

            if (keyIsHashed) {
                shardKeyLabel += ' (Hashed)';
            }

            shardKeyLabel += '</label>' + "<input type='hidden' name='shardkeys' value='" + shardKey + "' ";

            if (keyIsHashed) {
                shardKeyLabel += "hashed='true'";
            }

            shardKeyLabel += ">";

            shardKeyDirection = $('input[name="key_direction"]:checked', $('#' + formName)).val();
            console.log('shard key direction is ' + shardKeyDirection);

            $('#shard_key_pre').append('{' + shardKeyLabel + ': ' + keyDirection);
            $('#shardkeys').val('');
        }
    }
}

