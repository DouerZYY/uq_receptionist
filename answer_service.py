from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import tornado.ioloop
import tornado.web
import MySQLdb
import json


def connect_server():
    connection = MySQLdb.connect('localhost', 'root', '19941005', 'uq_receptionist')
    connection.set_character_set('utf8')
    connection.cursor().execute('SET NAMES utf8;')
    connection.cursor().execute('SET CHARACTER SET utf8;')
    connection.cursor().execute('SET character_set_connection=utf8;')
    return connection

response_body = {
    "speech": "",
    "displayText": "",
    "data": {},
    "contextOut": [],
    "source": "me"
}
# for stemmer
wnl = WordNetLemmatizer()


# get the keyword according to the original questions
def getKeywordFromText(text):
    text = text.lower()
    text = text.replace("?", "")
    text = text.replace("uq", "")
    text = text.replace('"', "")
    text = text.replace('(', "")
    text = text.replace(')', '')
    text = text.replace("what's", '')
    text = text.replace("'s", '')
    text = text.replace('.', '')
    text = text.replace('\n', '')
    words = text.split(" ")
    filtered_words = [word for word in words if word not in stopwords.words('english')]
    inserted = []
    for filtered in filtered_words:
        if filtered != "" and filtered not in inserted:
            inserted.append(filtered)
    return inserted

def compare_keyword(keywords_from_user, keywords, dataset):
    matched = []
    # finalList = []
    index = 0
    for row in keywords:
        matched.append(0)
        for keyword in keywords_from_user:
            # stemming the wordpytho
            keyword = wnl.lemmatize(keyword)
            if keyword in row:
                matched[index] += 1
        if matched[index] == 0:
            matched[index] = 0
        else:
            rate1 = (float(matched[index]) + 0) / (float(len(keywords_from_user)) + 0)
            rate2 = (float(matched[index]) + 0) / (float(len(row)) + 0 )
            matched[index] = rate1 + rate2
        # finalList.append(matched[index])
        index += 1

    sorted_x = sorted(range(len(matched)), key=lambda k: matched[k], reverse=True)
    print(matched[sorted_x[0]])
    index = sorted_x[0]
    print(index)
    if matched[index] >= 1.6:
        return dataset[index]['answer']
    else:
        return None


# fetch the value from parameter json expression
def getValueFromParameter(parameter):
    for key in parameter.keys():
        if parameter[key].encode('ASCII') != "":
            print(parameter[key])
            return parameter[key]
    return None

def fetchCourseInfoFromDataBase(name, field_name):
    connection = connect_server()
    cursor = connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('''SELECT * FROM course WHERE name=%s''', [name])
    result = cursor.fetchone()
    connection.close()
    if result is None:
        return 'No such course in UQ'
    return result[field_name]


# fetch all the data from database
def fetchAllDataFromDatabase(tablename):
    connection = connect_server()
    cursor = connection.cursor(MySQLdb.cursors.DictCursor)
    queryString = "SELECT * FROM %s" % tablename
    cursor.execute(queryString)
    result = cursor.fetchall()
    connection.close()
    if result is None:
        return None
    return result

# if the fetch fail, learn from the user input
def storeNewQuestionAndAnswer(question, answer):
    connection = connect_server()
    keyword = getKeywordFromText(question)
    connection.cursor().execute('''INSERT into self_training_question (question, answer, keyword)
                values (%s, %s, %s)''', [question, answer, ','.join(keyword)])
    connection.commit()
    all_keywords_in_self_train.append(keyword)
    all_self_train_questions.append({'question': question, 'answer': answer})
    connection.close()

def storeUserIntoDatabase(device_id, nationality):
    connection = connect_server()
    cursor = connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('''INSERT into user (device_id, nationality)
                values (%s, %s)''', [device_id, nationality])
    connection.commit()
    connection.close()


def fetchInfoFromDatabase(table_name, field_name, filter_name, filter_value):
    connection = connect_server()
    cursor = connection.cursor(MySQLdb.cursors.DictCursor)
    print(filter_value)
    queryString = "SELECT * FROM %s WHERE %s='%s'" % (table_name, filter_name, filter_value)
    cursor.execute(queryString)
    result = cursor.fetchone()
    connection.close()
    if result is None:
        return None
    return result[field_name]


# process ask for the unit of a course
def fetchUnitFromDatabase(parameter):
    name = getValueFromParameter(parameter)
    result = fetchCourseInfoFromDataBase(name, 'unit')
    return result


# process ask for the description of a course
def fetchDescriptionFromDatabase(parameter):
    name = getValueFromParameter(parameter)
    result = fetchCourseInfoFromDataBase(name, 'description')
    return name, result

# process ask for the description of a course
def fetchCoordinatorFromDatabase(parameter):
    name = getValueFromParameter(parameter)
    result = fetchCourseInfoFromDataBase(name, 'coordinator')
    return name, result


def fetchSchoolLocationFromDatabase(parameter, original_question):
    name = getValueFromParameter(parameter)
    if name is None:
        return name, process_general_question(original_question)
    result = fetchInfoFromDatabase('school', 'location', 'name', name)
    return name, result


def fetchSchoolEmailFromDatabase(parameter):
    name = getValueFromParameter(parameter)
    result = fetchInfoFromDatabase('school', 'email', 'name', name)
    return name, result


def fetchSchoolPhoneFromDatabase(parameter):
    name = getValueFromParameter(parameter)
    result = fetchInfoFromDatabase('school', 'phone', 'name', name)
    return name, result


# process request ask for some general questions
def process_general_question(original_question):
    keyword = getKeywordFromText(original_question)
    result = fetchInfoFromDatabase('self_training_question', 'answer', 'question', original_question)
    if result is None:
        result = compare_keyword(keyword, all_keywords, all_general_questions)
    else:
        result = "According to the user's knowledge: " + result
    # result = fetchInfoFromDatabase('general_question', 'answer', 'keyword', keyword)
    return result


def process_program_question(fieldName, parameter, context):
    print(fieldName)
    device_id = context['parameters']['deviceId']
    user_info = fetchInfoFromDatabase('user', 'nationality', 'device_id', device_id)
    if user_info is None:
        return 'no device', "Are you an international student?"
    if user_info == 1:
        title = getValueFromParameter(parameter)
        return title, fetchInfoFromDatabase('program_international', fieldName, 'title', title)
    else:
        title = getValueFromParameter(parameter)
        return title, fetchInfoFromDatabase('program_domestic', fieldName, 'title', title)

# switch to the function according to
def process_request(intent_type, parameter, original_question, context):
    if intent_type == 'CourseDescriptionIntent':
        name, result = fetchDescriptionFromDatabase(parameter)
        return result
    elif intent_type == 'CourseUnitIntent':
        name, result = fetchUnitFromDatabase(parameter)
        if result != 'No Such course in uq':
            result = 'The unit of ' + name + ' is: ' + result
        return result
    elif intent_type == 'DefaultFallbackIntent':
        result = process_general_question(original_question)
        return result
    elif intent_type == 'LocationIntent':
        name, result = fetchSchoolLocationFromDatabase(parameter, original_question)
        if result is not None:
            result = 'The location of ' + name + ' is: ' + result
        return result
    elif intent_type == 'LecturerIntent':
        name, result = fetchCoordinatorFromDatabase(parameter)
        if result is not None:
            result = 'The lecturer of ' + name + ' is: ' + result
        return result
    elif intent_type == 'GeneralIntent':
        result = process_general_question(original_question)
        return result
    elif intent_type == 'EntryRequirementIntent':
        name, result = process_program_question('entry_requirements', parameter, context)
        if result is not None and result != 'Are you an international student?':
            result = 'The entry requirements of ' + name + ' is: ' + result
        return result
    elif intent_type == 'ProgramCostIntent':
        name, result = process_program_question('fee', parameter, context)
        if result is not None and result != 'Are you an international student?':
            result = 'The cost of ' + name + ' is: ' + result + ' dollar per year'
        return result
    elif intent_type == 'ProgramDurationIntent':
        name, result = process_program_question('duration', parameter, context)
        if result is not None and result != 'Are you an international student?':
            result = 'The duration of ' + name + ' is: ' + result
        return result
    elif intent_type == 'ProgramCourseListIntent':
        name, result = process_program_question('courses', parameter, context)
        if result is not None and result != 'Are you an international student?':
            result = 'The course list of ' + name + ' is: ' + result
        return result
    else:
        return "Sorry, currently we do not have such service"


class MainHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')

    def get(self):
        self.write("Hello, world")

    def post(self):
        self.set_header("Content-Type", "text/plain")
        data = json.loads(self.request.body.decode('ascii'))
        print(data)
        result = data['result']
        parameter = result['parameters']
        if len(result['contexts']) > 0:
            context = result['contexts'][0]
        else:
            context = ""
        intentType = result['metadata']['intentName']
        original_question = result['resolvedQuery']

        result = process_request(intentType, parameter, original_question, context)
        print(result)
        if result is None:
            result = 'Sorry, we could not answer this question.'
        response = response_body
        response['speech'] = result
        response['displayText'] = result
        self.write(response)


# handle self training
class SelfTraingingHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')

    def get(self):
        self.write("Hello, world")

    def post(self):
        self.set_header("Content-Type", "text/plain")
        data = json.loads(self.request.body.decode('ascii'))
        print(data)
        question = data['question']
        answer = data['answer']

        storeNewQuestionAndAnswer(question, answer)
        response = {
            'result': 'We already record your request.'
        }
        self.write(response)

# handle self training
class UserHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')

    def get(self):
        self.write("Hello, world")

    def post(self):
        self.set_header("Content-Type", "text/plain")
        data = json.loads(self.request.body.decode('ascii'))
        print(data)
        device_id = data['deviceId']
        nationality = data['nationality']
        if nationality == '1':
            nationality = 1
        else:
            nationality = 0
        storeUserIntoDatabase(device_id, nationality)
        response = {
            'result': 'Store the user in database'
        }
        self.write(response)


def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/selftraining", SelfTraingingHandler),
        (r"/nationality", UserHandler)
    ])

def prepare_keyword():
    temp = []
    for row in all_general_questions:
        keywords = row['keyword'].split(',')
        processed_keywords = []
        for keyword in keywords:
            keyword = wnl.lemmatize(keyword)
            print(keyword)
            processed_keywords.append(keyword)
        all_keywords.append(processed_keywords)
    for row in all_self_train_questions:
        temp.append(row)
        keywords = row['keyword'].split(',')
        all_keywords_in_self_train.append(keywords)


all_general_questions = fetchAllDataFromDatabase('general_question')
all_self_train_questions = list(fetchAllDataFromDatabase('self_training_question'))
all_keywords = []
all_keywords_in_self_train = []
prepare_keyword()


if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
