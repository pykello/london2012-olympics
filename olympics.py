#!/usr/bin/python
import jinja2
from lxml import html
import sys
import os
import urllib2

import data

# ----------------------------------------------------------------------------
DIR = os.path.dirname(__file__)

BASE_URL = "http://www.telegraph.co.uk"
MEDALS_URL = "http://www.telegraph.co.uk/sport/olympics/medals/"

TEMPLATES_DIR = os.path.join(DIR, "templates")

TEMPLATES = {
    'population': "population.html",
    'gdp': "gdp.html",
}

OUTPUT_FILES = {
    'population': os.path.join(DIR, "output/ranking-population.html"),
    'gdp': os.path.join(DIR, "output/ranking-gdp.html"),
}


# ----------------------------------------------------------------------------
def main():
    medals = get_medals_data()

    population_adjuster = PopulationAdjustmentSystem(medals)
    population_adjusted_table = population_adjuster.adjusted_medals_table()

    render_page(template=TEMPLATES['population'],
                output_file=OUTPUT_FILES['population'],
                data={
                    'population': data.population,
                    'records': population_adjusted_table,
                })

    gdp_adjuster = GDPAdjustmentSystem(medals)
    gdp_adjusted_table = gdp_adjuster.adjusted_medals_table()

    render_page(template=TEMPLATES['gdp'],
                output_file=OUTPUT_FILES['gdp'],
                data={
                    'gdp': data.gdp,
                    'records': gdp_adjusted_table,
                })


# ----------------------------------------------------------------------------
class BaseAdjustmentSystem(object):

    def __init__(self, medals):
        self.medals = medals

    def get_score(self, country, count):
        return count

    def get_expected_medal_count(self, country):
        return 0

    def adjusted_medals_table(self):
        result = []
        for rec in self.medals:
            country = rec['country']
            flag = rec['flag']
            gold, silver, bronze = rec['gold'], rec['silver'], rec['bronze']

            total_medals = gold + silver + bronze
            expected_medals = self.get_expected_medal_count(country)

            result.append({
                'flag': flag,
                'country': country,
                'adjusted_gold': self.get_score(country, gold),
                'adjusted_silver': self.get_score(country, silver),
                'adjusted_bronze': self.get_score(country, bronze),
                'gold': gold,
                'silver': silver,
                'bronze': bronze,
                'total_medals': total_medals,
                'expected_medals': expected_medals,
            })

        key_function = lambda x:\
            (x['adjusted_gold'], x['adjusted_silver'], x['adjusted_bronze'])

        result.sort(key=key_function)
        result.reverse()

        for rank, rec in zip(range(1, 300), result):
            rec['rank'] = rank

        return result


# ----------------------------------------------------------------------------
class PopulationAdjustmentSystem(BaseAdjustmentSystem):

    def __init__(self, medals):
        super(PopulationAdjustmentSystem, self).__init__(medals)

        self.medal_count = total_medal_count(medals)

        self.population_sum = 0
        for record in medals:
            self.population_sum += data.population[record['country']]

    def get_score(self, country, medal_count):
        base_population = data.population['China']
        country_population = data.population[country]
        score = (medal_count * base_population) / country_population

        return score

    def get_expected_medal_count(self, country):
        country_population = data.population[country]
        medal_count = self.medal_count
        population_sum = self.population_sum

        result = float(medal_count * country_population) / population_sum

        return result


# ----------------------------------------------------------------------------
class GDPAdjustmentSystem(BaseAdjustmentSystem):

    def __init__(self, medals):
        super(GDPAdjustmentSystem, self).__init__(medals)

        self.medal_count = total_medal_count(medals)

        self.gdp_sum = 0
        for record in medals:
            self.gdp_sum += data.gdp[record['country']]

    def get_score(self, country, medal_count):
        base_gdp = data.gdp["United States"]
        country_gdp = data.gdp[country]
        score = (medal_count * base_gdp) / country_gdp

        return score

    def get_expected_medal_count(self, country):
        country_gdp = data.gdp[country]
        result = float(self.medal_count * country_gdp) / self.gdp_sum

        return result


# ----------------------------------------------------------------------------
def get_medals_data():
    medals = []
    page = urllib2.urlopen(MEDALS_URL, timeout=5).read()
    root = html.fromstring(page)
    rows = root.cssselect("#allMedals .odd, #allMedals .even")

    for row in rows:
        country = row.cssselect(".country")[0].text
        gold = int(row.cssselect(".gold")[0].text)
        silver = int(row.cssselect(".silver")[0].text)
        bronze = int(row.cssselect(".bronze")[0].text)
        flag = BASE_URL + row.cssselect(".country img")[0].attrib['src']

        medals.append(dict(country=country, gold=gold, silver=silver,
                           bronze=bronze, flag=flag))

    return medals


# ----------------------------------------------------------------------------
def total_medal_count(medals):
    medal_count = 0
    for record in medals:
        medal_count += record['gold']
        medal_count += record['silver']
        medal_count += record['bronze']

    return medal_count


# ----------------------------------------------------------------------------
def render_page(template, data, output_file):
    environment = jinja2.environment.Environment()
    environment.loader = jinja2.FileSystemLoader(TEMPLATES_DIR)

    template_object = environment.get_template(template)

    output = template_object.render(**data)

    output_file = open(output_file, "w")
    output_file.write(output)
    output_file.close()


# ----------------------------------------------------------------------------
if __name__ == "__main__":
    main()
