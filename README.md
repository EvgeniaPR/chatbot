## Описание

Toxibot – бот-модератор чатов, который присылает предупреждения участникам чата за токсичные комментарии, а также банит пользователя после третьего предупреждения.
Бот добавляется администратором в чат с помощью кнопки. Бота необходимо сделать администратором чата.
Все сообщения сканируются на постоянной основе и с помощью модели Hugging Face (SkolkovoInstitute/russian_toxicity_classifier) выносится вердикт – токсичное сообщение или нет.
Также администратор чата может отправить боту «запрещенные слова», после которых действуют такие же правила, как и после сканирования сообщения на токсичность.
Создается база данных, в которой ведется статистика :
 - Таблица со всеми чатами и запрещенными словами в каждом чате
 - Таблица со всеми пользователями чата и счетчиком их токсичных сообщений

## Команды

Для начала работы вызовите команду /start

Для создания, дополнения списка запрещенных слов введите команду /addbanwords прямо в чате, куда добавлен бот

Для удаления запрещенных слов из вашего списка введите команду /delbanwords прямо в чате, куда добавлен бот

Для удаления всех запрещенных слов введите команду /delallbanwords прямо в чате, куда добавлен бот

Для просмотра всех запрещенных слов введите команду /showbanwords прямо в чате, куда добавлен бот

## Библиотеки
- Библиотека pyTelegramBotAPI для создания бота телеграм
- Библиотека Transformers для подключения к модели Hugging Face через pipeline
- Модель SkolkovoInstitute/russian_toxicity_classifier - NLP classification
- Библиотека SQLite3 для хранения базы данных

