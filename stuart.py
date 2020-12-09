
import datetime

date = datetime.date.today()

print(date)

from moncli import create_column_value, ColumnType

col = create_column_value(id='date36', column_type=ColumnType.date, date=date)