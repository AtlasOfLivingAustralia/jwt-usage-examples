// Groovy Rest Client.
// > update user generated token file - keys_exmaple.json or add a new file.
// > update config - config.json if required
// > export PATH=$PATH:<<path to groovy folder>>/groovy-2.4.7/bin
// > cd <<path to this script>>
// > groovy RestClient.groovy
// To get the example post data, enable debugger at this.save and print the variable or right click and store as global variable.
// variable json string data will be printed in the console
// Use http://jsonformatter.org/ to format the data. (make sure to remove the " " around the string...)

import groovy.json.JsonSlurper
import com.auth0.jwt.*;
@Grapes([
        @Grab('org.apache.poi:poi:3.10.1'),
        @Grab(group = 'commons-codec', module = 'commons-codec', version = '1.9'),
        @Grab('org.apache.poi:poi-ooxml:3.10.1'),
        @Grab('com.auth0:java-jwt:3.18.3')]
)
import org.apache.poi.xssf.usermodel.XSSFWorkbook
import org.apache.poi.ss.usermodel.*
import java.nio.file.Paths
import java.text.DecimalFormat

// Import Configuration
def DEBUG_AND_VALIDATE = false;
def PROJECT_ID = "9c55416c-f56a-4917-a65e-da1d64a851f7"
def PROJECT_ACTIVITY_ID = "6fc5f8c1-1063-43f0-9d33-cbaf6ca2065f"
def xlsx = "coralWatch.xlsx"

def SERVER_URL = "https://biocollect-test.ala.org.au"
def APIG_URL = "https://apis.test.ala.org.au/biocollect"
def SPECIES_URL = "/search/searchSpecies/${PROJECT_ACTIVITY_ID}?limit=1&hub=coralwatch&dataFieldName=coralSpecies&output=CoralWatch"
def ADD_NEW_ACTIVITY_URL = "/ws/bioactivity/save?pActivityId=${PROJECT_ACTIVITY_ID}"
def SITE_LIST = '/site/ajaxList'

def header = []
def values = []

FormulaEvaluator evaluator

def keys = read_token_file()
def config = read_config_file()

println("Reading ${xlsx} file")

Paths.get(xlsx).withInputStream { input ->
    def workbook = new XSSFWorkbook(input)
    evaluator = workbook.getCreationHelper().createFormulaEvaluator()
    def sheet = workbook.getSheetAt(0)

    for (cell in sheet.getRow(0).cellIterator()) {
        header << cell.stringCellValue
    }

    def headerFlag = true

    Iterator<Row> allRows = sheet.rowIterator()
    while (allRows.hasNext()) {
        Row row = allRows.next()
        if (headerFlag) {
            headerFlag = false
            continue
        }

        if(row._cells[0].toString() == ""){
            break
        }

        def rowData = [:]
        rowData << ["rowNumber" : row.getRowNum() + 1]
        for (cell in row.cellIterator()) {
            def value = ''

            switch (cell.cellType) {
                case Cell.CELL_TYPE_STRING:
                    value = cell.stringCellValue
                    break
                case Cell.CELL_TYPE_NUMERIC:
                    if (org.apache.poi.hssf.usermodel.HSSFDateUtil.isCellDateFormatted(cell)) {
                        value = cell.getDateCellValue()
                    } else {
                        value = cell.numericCellValue as String
                    }

                    break
                case Cell.CELL_TYPE_BLANK:
                    value = ""
                    break
                case Cell.CELL_TYPE_BOOLEAN:
                    value = cell.booleanCellValue
                    break
                case Cell.CELL_TYPE_FORMULA:
                    value = evaluator.evaluate(cell)._textValue
                    break
                default:
                    println("Error: Cell type not supported..")
                    value = ''
            }

            rowData << [("${header[cell.columnIndex]}".toString()): value]
        }
        values << rowData
    }

    println("Successfully loaded ${xlsx} file");
    // Group same elements in to an array.
    def nestedActivities = []
    def processedIds = []

    println("Combining records");
    values?.each { entry ->
        def alreadyProcessed = processedIds.findAll { entry."Survey" == it }
        if (!alreadyProcessed) {
            def combinedRecords = values?.findAll {
                it."Survey" == entry."Survey" &&
                        it."Date" == entry."Date" &&
                        it."Reef Name" == entry."Reef Name"
            }

            DecimalFormat decimalFormat = new DecimalFormat("#")
            int intNum = decimalFormat.parse(entry."Number of records").intValue()
            if (combinedRecords.size() != intNum) {
                //some records have multiple sites

                def totalRecords = values?.findAll {it."Survey" == entry."Survey"}

                if(totalRecords.size() != intNum){
                    println("Error in survey " + entry."Survey")
                    println("Total record count should be ${intNum} but only ${totalRecords.size()} were found.")
                }

                def sites = totalRecords."Reef Name".unique()
                for(int i=0; i<sites.size(); i++){
                    combinedRecords = totalRecords.findAll{ item -> item."Reef Name" == sites[i]}
                    processedIds << totalRecords[0]."Survey"
                    nestedActivities << combinedRecords
                }
            }

            else {
                processedIds << combinedRecords[0]."Survey"
                nestedActivities << combinedRecords
            }
        }
    }

    println("Records nested under activities");
    println("Total activities = ${nestedActivities?.size()}")

    // Load default activity template file
    String jsonStr = new File('test_coralwatch_template.json').text

    // Loop through the activities
    nestedActivities?.eachWithIndex { activityRow, activityIndex ->

        def jsonSlurper = new groovy.json.JsonSlurper()
        def activity = jsonSlurper.parseText(jsonStr)

        println("***************")
        println("Building activity: ${activityIndex + 1 }  with records : ${activityRow?.size()} and starting excel row number : ${activityRow[0]."rowNumber"}")

        activity.projectId = PROJECT_ID

        activityRow?.eachWithIndex { record, idx ->
            TimeZone tz = TimeZone.getTimeZone("UTC");
            java.text.DateFormat df = new java.text.SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'"); // Quoted "Z" to indicate UTC, no timezone offset
            df.setTimeZone(tz);
            java.text.DateFormat time = new java.text.SimpleDateFormat("hh:mm a");
            String isoDate = ''
            String isoDateTime
            try{
                isoDate = df.format(record."Date")
                isoDateTime = record."Time" ? time.format(record."Time") : ""
            } catch (Exception ex){
                println("Date format error ${record."Survey"}")
            }

            // Map generic fields
            if (idx == 0) {
                def siteId = "";

                //check site

                def siteCheckNameConnection = new URL("${SERVER_URL}${SITE_LIST}?id=${PROJECT_ACTIVITY_ID}&entityType=projectActivity").openConnection() as HttpURLConnection
                keys = get_token(config, keys)
                siteCheckNameConnection.setRequestProperty("Authorization","Bearer "+ keys.access_token)
                siteCheckNameConnection.setRequestProperty('Content-Type', 'application/json;charset=utf-8')
                siteCheckNameConnection.setRequestMethod("GET")
                siteCheckNameConnection.setDoOutput(true)

                def statusCode = siteCheckNameConnection.responseCode
                if (statusCode == 200 ){
                    def list = siteCheckNameConnection.inputStream.text;
                    def site_list = new JsonSlurper().parseText(list)

                    if(site_list.name.contains(record."Reef Name")) {
                        siteId = site_list.find{ it.name == record."Reef Name"}.siteId
                    }
                    else {
                        println("Came hereeeeeeeeeeeeeeeeeee")
                    }

                } else {
                    def error = siteCheckNameConnection.getErrorStream().text
                    println(siteCheckNameConnection.responseCode + " : " + error)
                    def result = new JsonSlurper().parseText(error)

                }

                activity.siteId = siteId
                activity.outputs[0].data.groupName = record."Group Name"
                activity.outputs[0].data.groupType = record."Participating As"
                activity.outputs[0].data.countryOfSurvey = record."Country of Survey"
                activity.outputs[0].data.recordedBy = record."Creator"
                activity.outputs[0].data.eventDate = isoDate
                activity.outputs[0].data.eventTime = isoDateTime
                activity.outputs[0].data.lightCondition = record."Light Condition"
                activity.outputs[0].data.depthInMetres = record."Depth (m)" ?: record."Depth (ft)" ? footToMeter(Double.parseDouble(record."Depth (ft)")) : 0
                activity.outputs[0].data.depthInFeet = record."Depth (ft)" ?: record."Depth (m)" ? meterToFoot(Double.parseDouble(record."Depth (m)")) : 0
                activity.outputs[0].data.waterTemperatureInDegreesCelcius = record."Water Temperature (C)" ?: record."Water Temperature (F)" ? farenheitToCelcius(Double.parseDouble(record."Water Temperature (F)")): 0
                activity.outputs[0].data.waterTemperatureInDegreesFarenheit = record."Water Temperature (F)" ?: record."Water Temperature (C)" ? celciusToFarenheit(Double.parseDouble(record."Water Temperature (C)")): 0
                activity.outputs[0].data.activity = record."Activity"
                activity.outputs[0].data.eventRemarks = record."Comments"
                activity.outputs[0].data.gpsDeviceUsed = record."I used a GPS" == "yes"

                activity.outputs[0].data.location = siteId
                activity.outputs[0].data.locationLatitude = record."Latitude"
                activity.outputs[0].data.locationLongitude = record."Longitude"
                activity.outputs[0].data.locationHiddenLatitude = record."Latitude"
                activity.outputs[0].data.locationHiddenLongitude = record."Longitude"
                activity.outputs[0].data.overallAverage = record."Average overall"
            }

            if(activity) {

                def coralObservations = []
                def species = [name: '', guid: '', scientificName: '', commonName: '', outputSpeciesId: '', listId: '']

                if (record.'Coral Species') {
                    def list = record.'Coral Species'.split(",")

                    if (list.size() == 1) {

                        // Get Unique Species Id
                        def uniqueIdResponse = new URL(APIG_URL + "/ws/species/uniqueId")?.text
                        def jsonResponse = new groovy.json.JsonSlurper()
                        def outputSpeciesId = jsonResponse.parseText(uniqueIdResponse)?.outputSpeciesId
                        species.outputSpeciesId = outputSpeciesId

                        // Get species name
                        def speciesResponse = new URL(SERVER_URL + SPECIES_URL + "&q=${list[0].replace(" sp.", "").replace(" ", "+").trim()}").text
                        def speciesJSON = new groovy.json.JsonSlurper()
                        def autoCompleteList = speciesJSON.parseText(speciesResponse)?.autoCompleteList

                        if (!autoCompleteList) {
                            species.name = list[0]
                        }

                        autoCompleteList?.eachWithIndex { item, index ->
                            if (index == 0) {
                                species.name = item.name
                                species.guid = item.guid
                                species.scientificName = item.scientificName
                                species.commonName = item.commonName
                                species.listId = item.listId
                            }
                        }
                    } else if (list.size() > 1 && idx == 0) {
                        def separator = activity.outputs[0].data.eventRemarks ? "; " : ""
                        activity.outputs[0].data.eventRemarks = activity.outputs[0].data.eventRemarks.concat("${separator}${record.'Coral Species'}")
                    }
                }

                coralObservations << [sampleId          : idx + 1,
                                      colourCodeLightest: record.'Lightest',
                                      colourCodeDarkest : record.'Darkest',
                                      colourCodeAverage : (Double.parseDouble(record.'Lightest Number') + Double.parseDouble(record."Darkest Number")) / 2,
                                      typeOfCoral       : record.'Coral Type' + " corals",
                                      coralSpecies      : species,
                                      speciesPhoto      : []]

                coralObservations?.each { coralObservation ->
                    activity.outputs[0].data.coralObservations << coralObservation
                }
            }

        }

        if(activity) {
            // post data via web service.
            def connection = new URL("${APIG_URL}${ADD_NEW_ACTIVITY_URL}").openConnection() as HttpURLConnection

            // set some headers
            keys = get_token(config, keys)
            connection.setRequestProperty("Authorization","Bearer "+ keys.access_token);
            connection.setRequestProperty('Content-Type', 'application/json;charset=utf-8')
            connection.setRequestMethod("POST")
            connection.setDoOutput(true)

            if (!DEBUG_AND_VALIDATE) {
                java.io.OutputStreamWriter wr = new java.io.OutputStreamWriter(connection.getOutputStream(), 'utf-8')
                wr.write(new groovy.json.JsonBuilder(activity).toString())
                wr.flush()
                wr.close()
                // get the response code - automatically sends the request
                println connection.responseCode + ": " + connection.inputStream.text
            }
        }

    }

    println("Completed..")
}

public static double footToMeter(double foot){
    return (foot * 0.3048).round(2)
}
public static double meterToFoot(double meter){
    return (meter / 0.3048).round(2)
}

public static double celciusToFarenheit(double celcius){
    return ((9.0/5.0)*celcius + 32).round(2)
}
public static double farenheitToCelcius(double farenheit){
    return ((5.0/9.0)*(farenheit - 32)).round(2)
}

public get_token(config, keys) {
//    if expired regenerate, else just return the access_token
    def decodedJWT = JWT.decode(keys.access_token)
    if( decodedJWT.getExpiresAt().before(new Date())) {
//        regenerate token
        println("Current token has expired. Refreshing token...")
        regenerate_token(config, keys)
    }
    return keys
}

public read_token_file(){

    String jsonStr = new File('../keys_exmaple.json').text
    def jsonSlurper = new JsonSlurper()
    def keys = jsonSlurper.parseText(jsonStr)

    return keys
}

public read_config_file(){

    String jsonStr = new File('./config.json').text
    def jsonSlurper = new JsonSlurper()
    def config = jsonSlurper.parseText(jsonStr)

    return config
}

public regenerate_token(config, keys) {

    String urlParameters  = "refresh_token=${keys.refresh_token}&grant_type=refresh_token&scope=${config.scope}"
    def postData = urlParameters.getBytes('utf-8')

    def connection = new URL(keys.token_url).openConnection() as HttpURLConnection
    // set some headers
    connection.setRequestProperty("Authorization","Basic "+ Base64.encoder.encodeToString((config.client_id + ":" + config.client_secret).bytes))
    connection.setRequestProperty('Content-Type', 'application/x-www-form-urlencoded')
    connection.setRequestMethod("POST")
    connection.setDoOutput(true)

    DataOutputStream wr = new DataOutputStream(connection.getOutputStream())
    wr.write(postData)
    wr.flush()
    wr.close()

    if (connection.responseCode == 200) {
        def response = new JsonSlurper().parseText(connection.inputStream.text)
        keys.access_token = response.access_token
        println("Token refreshed")
    }
    else{
        println("Unable to refresh access token. " + connection.responseCode)
    }

    return keys
}