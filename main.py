# Cameron Ela, ceela@usc.edu
# This program creates visualizations regarding goals scored and yellow cards received in
# UEFA Champions League (soccer) seasons from 2003-2004 to 2017-2018 (a csv that I made myself! :D)

import io
import os
import sqlite3 as sl

import numpy as np
import pandas as pd
from flask import Flask, redirect, render_template, request, session, url_for, send_file
from matplotlib import pyplot as plt
from sklearn.linear_model import LinearRegression as slr

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
db = "champions-league-data.db"


@app.route("/")
def home_new():
    options = {
        "scoring": "Goals Scored",
        "discipline": "Yellow Cards Given"
    }
    return render_template("home_new.html", years=db_get_years(), message="Please enter a year to search for.",
                           options=options)


@app.route("/submit_year", methods=["POST"])
def submit_year():
    print(request.form['year'])
    session["year"] = request.form["year"]
    if 'year' not in session or session["year"] == "":
        return redirect(url_for("home_new"))
    if "data_request" not in request.form:
        return redirect(url_for("home_new"))
    session["data_request"] = request.form["data_request"]
    return redirect(url_for("year_current", data_request=session["data_request"], year=session["year"]))


@app.route("/api/ucl/<data_request>/<year>")
def year_current(data_request, year):
    return render_template("year.html", data_request=data_request, year=year)


@app.route("/submit_projection", methods=["POST"])
def submit_projection():
    if 'year' not in session:
        return redirect(url_for("home_new"))
    session["year"] = request.form["year"]
    if session["year"] == "":
        return redirect(url_for("home_new"))
    return redirect(url_for("year_projection", year=session["year"], data_request="projection"))


@app.route("/api/ucl/<data_request>/projection/<year>")
def year_projection(year, data_request):
    session["data_request"] = data_request
    return render_template("year_project.html", year=year, data_request=data_request)


@app.route("/fig/<year>/<data_request>")
def fig(year, data_request):
    fig = create_figure(year, data_request)

    # img = io.BytesIO()
    # fig.savefig(img, format='png')
    # img.seek(0)
    # w = FileWrapper(img)
    # # w = werkzeug.wsgi.wrap_file(img)
    # return Response(w, mimetype="text/plain", direct_passthrough=True)

    img = io.BytesIO()
    fig.savefig(img, format='png')
    img.seek(0)
    return send_file(img, mimetype="image/png")


def create_figure(year, data_request):
    # for existing data
    print(data_request)
    if data_request != "projection":
        df = db_create_dataframe(year)
        print(session)
        # graph goals/yellow cards for each team in a year
        fig, ax = plt.subplots(1, 1)
        if session["data_request"] == "scoring":
            plt.suptitle(data_request.capitalize() + ": goals scored in " + year)
            ax.bar(df["Team"], df["GF"])
            tot_goals = df["GF"].sum()
            ax.set(title=f"Total Goals: {tot_goals}", xlabel="Team", ylabel="Goals Scored")
        else:
            plt.suptitle(data_request.capitalize() + ": yellow cards in " + year)
            ax.bar(df["Team"], df["Yellow"])
            tot_yellow = df["Yellow"].sum()
            ax.set(title=f"Total Yellow Cards: {tot_yellow}", xlabel="Team", ylabel="Yellow Cards")
        plt.xticks(rotation=90)
        plt.tight_layout()
        return fig
    # for projections
    else:
        columns = ["Year", "GF", "Yellow"]
        # create dataframe of aggregates
        df_agg = pd.DataFrame(columns=columns)
        for i in range(2004, 2019):
            df = db_create_dataframe(i)
            df = df.drop(columns=["Team", "Nation"])
            df = df.groupby("Year")[["GF", "Yellow"]].sum().reset_index()
            df_agg = pd.concat([df_agg, df], ignore_index=True)
        # conduct SLR
        model_goals = slr()
        model_yellow = slr()
        X = df_agg["Year"].values.reshape(-1, 1)   # reshape to adhere to .fit() requirements
        model_goals.fit(X, df_agg["GF"].values.reshape(-1, 1))
        model_yellow.fit(X, df_agg["Yellow"].values.reshape(-1, 1))
        project_years = np.array([x for x in range(int(year), int(year) + 5)])
        project_years = project_years.reshape(-1, 1)    # for use in prediction
        goals_pred = model_goals.predict(project_years)
        yellow_pred = model_yellow.predict(project_years)
        # graph SLR
        fig, ax = plt.subplots(1, 1)
        plt.suptitle("Goals scored and yellow cards projected from " + year + "-" + str(int(year) + 4))
        # "flatten" 2D arrays to be passed as 1D arrays
        ax.bar(project_years.flatten(), goals_pred.flatten(), linewidth=0.8, hatch="//", color="blue",
               label="Goals")
        ax.set(title="Goals/Yellow Cards", xlabel="Year", ylabel="Goals Scored/Yellow Cards Given")
        ax.bar(project_years.flatten(), yellow_pred.flatten(), linewidth=0.8, hatch="/", alpha=0.3, color="orange",
               label="Yellow Cards")
        ax.set_ylim(bottom=300)
        plt.legend()
        plt.tight_layout()
        return fig


def db_create_dataframe(year):
    conn = sl.connect(db)
    curs = conn.cursor()

    table = "ucl_data"
    print(f'{table=}')
    print(f'{year=}')
    # build DataFrame
    stmt = "SELECT Year, Team, Nation, GF, Yellow FROM " + table + " WHERE `Year`=?"
    data = curs.execute(stmt, (str(year),)).fetchall()
    columns = ["Year", "Team", "Nation", "GF", "Yellow"]
    dtypes = {"Year": int, "Team": str, "Nation": str, "GF": int, "Yellow": int}
    df = pd.DataFrame(data, columns=columns).astype(dtypes)
    conn.close()
    return df


def db_get_years():
    conn = sl.connect(db)
    curs = conn.cursor()

    table = "ucl_data"
    stmt = "SELECT `Year` from " + table
    data = curs.execute(stmt)
    # sort a set comprehension for unique values
    years = sorted({result[0] for result in data})
    conn.close()
    return years


@app.route('/<path:path>')
def catch_all(path):
    return redirect(url_for("home_new"))


if __name__ == "__main__":
    print(db_get_years())
    app.secret_key = os.urandom(12)
    app.run(debug=True)
