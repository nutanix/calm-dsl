class TASK_INPUT:
    class TYPE:
        TEXT = "text"
        PASSWORD = "password"
        CHECKBOX = "checkbox"
        SELECT = "select"
        SELECTMULTIPLE = "selectmultiple"
        DATE = "date"
        TIME = "time"
        DATETIME = "datetime"

    VALID_TYPES = [
        TYPE.TEXT,
        TYPE.PASSWORD,
        TYPE.CHECKBOX,
        TYPE.SELECT,
        TYPE.SELECTMULTIPLE,
        TYPE.DATE,
        TYPE.TIME,
        TYPE.DATETIME,
    ]
