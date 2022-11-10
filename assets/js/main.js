var speechRecognition = window.webkitSpeechRecognition
var recognition = new speechRecognition()
const validImageTypes = ['image/jpg', 'image/jpeg', 'image/png']

function click_search(){
    var value = $("#search-input").val()
    console.log('Click Search!')
    console.log(value)
    $("#search-input").val("")
    value = value.replaceAll(' ', '_')
    console.log(value)
    var params = {
        'q': value,
    }
    sdk.searchGet(params, {}, {}).then(function(result){
        console.log(result)
        var data = result.data;
        $("#album-div").html("")
        if (data.results.length > 0) {
            for (let i = 0; i < data.results.length; i++) {
                var image = $("<img class='album-image'>")
                image.attr("src", data.results[i]['url'])
                $("#album-div").append(image)
              } 
        }
    }).catch( function(result){
        console.log(result)
        $("#album-div").html("")
    })
}


  
function upload(){
    var files = $('#upload-button').prop('files')
    if (files.length == 0) {
        $('#upload-status').text("Please select an image")
    } else{
        var file = files[0]
        var file_name = file.name
        var file_type = file['type']
        var form_data = new FormData()
        var custom_label = $('#label-input').val()
        form_data.append("file", file)
        
        console.log(file)
        console.log(file_name)
        console.log(file_type)

        if (!validImageTypes.includes(file_type)) {
            $('#upload-status').text("Not an image. Upload files ending with .jpg, .jpeg, or .png")
        } else {
            var reader = new FileReader();
            var params = {
                'filename': file_name,
                'bucket': "bucket-album",
                'x-amz-meta-customLabels': custom_label,
                "Content-Type" : "image/jpeg"
            }
            reader.onload = function(event) {
                const file =  new Uint8Array(event.target.result)
                file.constructor = () => file;
                sdk.uploadBucketFilenamePut(
                    params, file, {} 
                ).then(function(result){
                    console.log(result)
                    $('#label-input').val("")
                    $('#upload-status').text("Upload is successful")
                }).catch(function(result){
                    console.log(result)
                    $('#upload-status').text("Upload is error")
                })
            };
            reader.readAsArrayBuffer(file);
        }
    }
}

function start_text(){
    $("#stop-button").show()
    $("#record-button").hide()
    recognition.start()
    recognition.onresult = function(event) {
        var current = event.resultIndex;
        var transcript = event.results[current][0].transcript
        $("#search-input").val(transcript)
    }
    $("#record-button").show()
    $("#stop-button").hide()
}

function finish_text(){
    recognition.stop();
    recognition.onresult = function(event) {
        var current = event.resultIndex;
        var transcript = event.results[current][0].transcript
        $("#search-input").val(transcript)
    }
    $("#record-button").show()
    $("#stop-button").hide()
}

$( document ).ready(function() {
    console.log('Start');
    $("#stop-button").hide()
    $("#search-button").click(function(){
        click_search();
    })
    $("#record-button").click(function(event) {
        start_text();
    })
    $("#stop-button").click(function(event) {
        finish_text();
    })
    $("#submit-button").click(function(event) {
        upload();
    })
})