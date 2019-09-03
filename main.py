import argparse
import datetime

import matplotlib.dates as dates
import matplotlib.lines as lines
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd

FIGURE_WIDTH = 10.8
FIGURE_HEIGHT = 7.2
DATA_ALPHA = 0.1
GRID_ALPHA = 0.33

SLEEP_TIME_TYPES = {
    'totalSleepTime': {'color': '#1f77b4', 'label': 'Total'},
    'shallowSleepTime': {'color': '#d62728', 'label': 'Shallow'},
    'deepSleepTime': {'color': '#9467bd', 'label': 'Deep'}
}


def load_data(file_path: str) -> pd.DataFrame:
    df = pd.read_csv(file_path, encoding='utf-8-sig')
    df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d')
    df['deepSleepTime'] = df['deepSleepTime'] / 60
    df['shallowSleepTime'] = df['shallowSleepTime'] / 60
    df['totalSleepTime'] = df['deepSleepTime'] + df['shallowSleepTime']
    df['start'] = pd.to_datetime(df['start'], unit='s')
    df['stop'] = pd.to_datetime(df['stop'], unit='s')
    return df


def filter_data(df: pd.DataFrame, after: datetime.datetime, before: datetime.datetime, exclude_weekends: bool) -> pd.DataFrame:
    if after is not None:
        # Keep rows after a date.
        df = df[df['date'] > after]
    if before is not None:
        # Keep rows before a date.
        df = df[df['date'] < before]
    if exclude_weekends:
        # Remove weekend rows.
        df = df[df['date'].dt.dayofweek < 5]
    return df


def initialize_plot():
    # Avoid "FutureWarning: Using an implicitly registered datetime converter for a matplotlib plotting method".
    pd.plotting.register_matplotlib_converters()
    plt.figure(figsize=(FIGURE_WIDTH, FIGURE_HEIGHT))


def plot_dots(df: pd.DataFrame, sleep_time_type: str, color: str):
    plt.plot(df['date'], df[sleep_time_type], alpha=DATA_ALPHA, color=color, linestyle='None', marker='.')


def plot_lines(df: pd.DataFrame, exclude_weekends: bool, sleep_time_type: str, color: str):
    hlines_df = df.copy()

    # Evaluate rolling means on every date.
    rolling_window = 5 if exclude_weekends else 7
    hlines_df['rollingMean'] = hlines_df[sleep_time_type].rolling(rolling_window).mean()

    # Once rolling means have been evaluated, only keep Monday rows.
    hlines_df = hlines_df[hlines_df['date'].dt.dayofweek == 0]

    # Each Monday row is represented by a line stretched on the whole week.
    for i, r in hlines_df.iterrows():
        plt.hlines(r['rollingMean'], r['date'] - datetime.timedelta(days=7), r['date'], colors=color)


def plot_average_line(df: pd.DataFrame, sleep_time_type: str, color: str):
    mean = df[sleep_time_type].mean()
    plt.axhline(y=mean, alpha=DATA_ALPHA, color=color, linestyle='--')


def render_plot(file_path: str):
    # xaxis configuration: Major ticks every month, minor ticks every week (+ these can overlap).
    plt.gca().xaxis.set_remove_overlapping_locs(False)
    plt.gca().xaxis.set_major_locator(dates.MonthLocator())
    plt.gca().xaxis.set_major_formatter(dates.DateFormatter('%Y-%m'))
    plt.gca().xaxis.set_minor_locator(dates.WeekdayLocator(byweekday=0))

    # xaxis configuration: Customize tick labels alignment for a subjectively more readable result.
    for tick in plt.gca().get_xticklabels():
        tick.set_ha('left')

    # yaxis configuration: Major ticks every hour, minor ticks every 10 minutes.
    plt.gca().yaxis.set_major_locator(ticker.MultipleLocator(1))
    plt.gca().yaxis.set_minor_locator(ticker.AutoMinorLocator(6))

    # yaxis configuration: Start at 0 to avoid displaying negative time.
    plt.ylim(bottom=0)

    # Grid configuration.
    plt.grid(b=True, which='major', linestyle='--')
    plt.grid(b=True, which='minor', linestyle=':', alpha=GRID_ALPHA)

    # Legend configuration.
    legend_elements = []
    for k, v in SLEEP_TIME_TYPES.items():
        legend_elements.append(lines.Line2D([0], [0], color=v['color'], label=v['label']))
    plt.legend(handles=legend_elements)
    plt.xlabel('Date')
    plt.ylabel('Sleep time (h)')

    plt.savefig(file_path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('sleep_data_file', metavar='sleep-data-file-path', type=argparse.FileType('r'))
    parser.add_argument('output_file', metavar='output-file-path', type=argparse.FileType('w'))
    parser.add_argument('--after', type=lambda d: datetime.datetime.strptime(d, '%Y-%m-%d'))
    parser.add_argument('--before', type=lambda d: datetime.datetime.strptime(d, '%Y-%m-%d'))
    parser.add_argument('--exclude-weekends', action='store_true')
    args = parser.parse_args()

    df = load_data(args.sleep_data_file.name)
    df = filter_data(df, args.after, args.before, args.exclude_weekends)

    initialize_plot()
    for k, v in SLEEP_TIME_TYPES.items():
        plot_dots(df, k, v['color'])
        plot_lines(df, args.exclude_weekends, k, v['color'])
        plot_average_line(df, k, v['color'])
    render_plot(args.output_file.name)


if __name__ == '__main__':
    main()
