"""
Функции для формирования выходной информации.
"""

import datetime
from decimal import ROUND_HALF_UP, Decimal

from prettytable import PrettyTable

from collectors.models import LocationInfoDTO


class Renderer:
    """
    Генерация результата преобразования прочитанных данных.
    """

    def __init__(self, location_info: LocationInfoDTO) -> None:
        """
        Конструктор.

        :param location_info: Данные о географическом месте.
        """

        self.location_info = location_info

    async def render(self) -> tuple[str, ...]:
        """
        Форматирование прочитанных данных.

        :return: Результат форматирования
        """

        return tuple(await self._format_as_table())

    async def _format_as_table(self) -> list[str]:
        """
        Форматирование прочитанных данных в табличный формат.

        :return: Результат форматирования
        """

        table = PrettyTable()
        table.field_names = [
            "Название",
            "Регион",
            "Площадь (м^2)",
            "Языки",
            "Население (чел.)",
            "Название столицы",
            "Координаты",
            "Текущее время",
            "Часовой пояс",
            "Курсы валют (руб.)",
            "Описание",
            "Температура (°C)",
            "Видимость (м)",
            "Скорость ветра (м/с)",
        ]
        table.add_row(
            [
                await self.split_country_name(self.location_info.location.name),
                self.location_info.location.subregion,
                self.location_info.location.area,
                await self._format_languages(),
                await self._format_population(),
                self.location_info.location.capital,
                f"({self.location_info.capital_location.lat}, {self.location_info.capital_location.lon})",
                await self._format_time(),
                await self._format_timezone(),
                await self._format_currency_rates(),
                self.location_info.weather.description,
                self.location_info.weather.temp,
                self.location_info.weather.visibility,
                self.location_info.weather.wind_speed,
            ]
        )
        groups = await self._format_table_groups(
            table.get_string(), ["Страна", "Столица", "Валюта", "Погода"], [5, 4, 1, 4]
        )
        return [
            groups,
            table.get_string(),
            "Последние новости:",
            await self._format_news(),
        ]

    async def split_country_name(self, country_name: str) -> str:
        """
        Разделение названия страны на 2 строки

        :param country_name: Название страны
        :return: Результат форматирования
        """

        space_pos = -1
        mid_pos = len(country_name) // 2
        for i in range(mid_pos, len(country_name)):
            if country_name[i] == " ":
                space_pos = i
                break
        if space_pos == -1:
            return country_name
        return (
            country_name[:space_pos]
            + "\n"
            + country_name[space_pos + 1 : len(country_name)]
        )

    async def _format_table_groups(
        self,
        table_string: str,
        column_groups_names: list[str],
        column_groups_length: list[int],
        corner_sep: str = "+",
        column_sep: str = "|",
        row_char: str = "-",
    ) -> str:
        """
        Создание колонок-названий групп по длине отформатированной таблицы

        :param table_string: строковое представление отфомратированной табличной информации
        :param column_groups_names: список названий групп колонок в порядке расположения в таблице
        :param column_groups_length: список количества колонок, которые входят в каждую группу,
        длина списка должна быть равна длине списка названий, сумма всех
        значений должна быть равна количеству колонок в таблице
        :param corner_sep: символ угла в таблице
        :param column_sep: символ разделителя столбца в таблице
        :param row_char: символ разделителя строки в таблице

        :return: Результат форматирования
        """

        cols = table_string.split("\n")[0].split(corner_sep)[1:]
        column_lengths = [len(c) for c in cols]
        res = ""
        upper_boudary = ""
        group_col_names = ""
        col_index = 0
        for i in range(len(column_groups_length)):
            group_col_length = sum(
                [
                    column_lengths[ci]
                    for ci in range(col_index, column_groups_length[i] + col_index)
                ]
            )
            inner_corner_sep_amount = column_groups_length[i] - 1
            group_col_length += inner_corner_sep_amount
            upper_boudary += (
                f'{corner_sep}{"".join([row_char for ch in range(group_col_length)])}'
            )
            empty_space_in_gr_name_left = (
                group_col_length - len(column_groups_names[i])
            ) // 2
            group_col_names += f'{column_sep}{"".join([" " for ch in range(empty_space_in_gr_name_left)])}'
            group_col_names += f"{column_groups_names[i]}"
            empty_space_in_gr_name_right = (
                group_col_length
                - len(column_groups_names[i])
                - empty_space_in_gr_name_left
            )
            group_col_names += (
                f'{"".join([" " for ch in range(empty_space_in_gr_name_right)])}'
            )
            col_index += column_groups_length[i]
            col_index += column_groups_length[i]
        upper_boudary += corner_sep
        group_col_names += column_sep
        res = f"{upper_boudary}\n{group_col_names}"
        return res

    async def _format_time(self) -> str:
        """
        Форматирование информации о времени в столице.

        :return:
        """
        if (
            self.location_info.capital_location.timezone
            and self.location_info.capital_location.current_time_UTC
        ):
            capital_time_unix = int(
                self.location_info.capital_location.current_time_UTC
            ) + int(self.location_info.capital_location.timezone)
            capital_time = datetime.datetime.utcfromtimestamp(
                capital_time_unix
            ).strftime("%Y-%m-%dT%H:%M:%SZ")
            return f"{capital_time}"
        return "Информации о времени нет"

    async def _format_news(self) -> str:
        """
        Форматирование информации о новости.

        :return:
        """
        res = ""
        if self.location_info.news.news:
            for news in list(self.location_info.news.news):
                res += (
                    f"Источнк: {news.source_name}\n{news.published_at}\n{news.author}:"
                )
                res += f"{news.title}\nURL:{news.url}\n\n"
        return res

    async def _format_timezone(self) -> str:
        """
        Форматирование информации о часовом поясе в столице.

        :return:
        """
        seconds_in_hour = 3600
        if self.location_info.capital_location.timezone:
            timezone_utc = (
                int(self.location_info.capital_location.timezone) // seconds_in_hour
            )
            return f"UTC {timezone_utc}"
        return "Информации о часовом поясе нет"

    async def _format_languages(self) -> str:
        """
        Форматирование информации о языках.

        :return:
        """

        return ",\n".join(
            f"{item.name} ({item.native_name})"
            for item in self.location_info.location.languages
        )

    async def _format_population(self) -> str:
        """
        Форматирование информации о населении.

        :return:
        """

        # pylint: disable=C0209
        return "{:,}".format(self.location_info.location.population).replace(",", ".")

    async def _format_currency_rates(self) -> str:
        """
        Форматирование информации о курсах валют.

        :return:
        """

        return ",\n".join(
            f"{currency} = {Decimal(rates).quantize(exp=Decimal('.01'), rounding=ROUND_HALF_UP)}"
            for currency, rates in self.location_info.currency_rates.items()
        )
