#!/usr/bin/python

# A hacktastic script to extract the ADSL stats out of a Netgear DGN1000 modem/router.

import sys
import os
import re
import commands
import rrdtool
import time
from BeautifulSoup import BeautifulSoup


### Begin tweaking here

# Router login details
ip = '192.168.0.1'
username = 'admin'
password = 'ermantoroglu'

# RRD database
rrdfile = 'dslstat.rrd'

# Output directory
outdir = '/home/omer/dslstat'


### Functions and such...

# Strip out html and extract value
def strip_val(str):
  return re.sub('<[^<]+?>', '', str).split(' ')[0]


# Print key/value pairs of a dictionary
def print_stats(stats):
  for key, val in stats.items():
    print key + " : " + val


# Initialise the RRD database
def rrd_init():
  res = rrdtool.create(rrdfile, "--step", "300", "--start", '0',
      "DS:down_speed:GAUGE:600:U:U",
      "DS:up_speed:GAUGE:600:U:U",
      "DS:down_atten:GAUGE:600:U:U",
      "DS:up_atten:GAUGE:600:U:U",
      "DS:down_noise:GAUGE:600:U:U",
      "DS:up_noise:GAUGE:600:U:U",
      "RRA:AVERAGE:0.5:1:600",
      "RRA:AVERAGE:0.5:6:700",
      "RRA:AVERAGE:0.5:24:775",
      "RRA:AVERAGE:0.5:288:797",
      "RRA:MAX:0.5:1:600",
      "RRA:MAX:0.5:6:700",
      "RRA:MAX:0.5:24:775",
      "RRA:MAX:0.5:444:797")
 
  if res:
    print rrdtool.error()


# Update the RRD database
def rrd_update(stats):
  res = rrdtool.update(rrdfile,
                        'N:' + stats['down_speed'] + ':' + stats['up_speed']
                      + ':' + stats['down_atten'] + ':' + stats['up_atten']
                      + ':' + stats['down_noise'] + ':' + stats['up_noise'])
  
  if res:
    print rrdtool.error()


# Generate fancy graphs out of the RRD database
def rrd_generate():
  res = rrdtool.graph( outdir + "/adsl-daily.png", "--start", "-1d", "--title=ADSL Sync Speed (Daily)", "--vertical-label=kilobytes/s",
      "DEF:down_speed=" + rrdfile + ":down_speed:AVERAGE",
      "DEF:up_speed=" + rrdfile + ":up_speed:AVERAGE",
      "LINE1:down_speed#00FF00:Downstream Sync Speed",
      "LINE1:up_speed#0000FF:Upstream Sync Speed\\r",
      "COMMENT:\\n",
      "GPRINT:down_speed:AVERAGE:Avg Down Speed\: %5.lfkbps",
      "COMMENT: ",
      "GPRINT:down_speed:MAX:Max Down Speed\: %5.lfkbps\\r",
      "GPRINT:up_speed:AVERAGE:Avg Up Speed\: %5.lfkbps",
      "COMMENT:   ",
      "GPRINT:up_speed:MAX:Max Up Speed\: %5.lfkbps\\r")

  if res:
    print rrdtool.error()


# Grab stats from the router and return it in the form of a dictionary
def grab_stats():
  # Probably could have used urllib here, but hey...
  res = commands.getstatusoutput('curl -s http://' + username + ':' + password + '@' + ip + '/stattbl.htm | sed -n 84,105p')

  soup = BeautifulSoup(res[1])

  # Voodoo!
  values = [ [ col.renderContents() for col in row.findAll('td') ] for row in soup.find('table').findAll('tr') ]

  return { 'down_speed' : strip_val(values[1][1]),
           'up_speed' : strip_val(values[1][2]),
           'down_atten' : strip_val(values[2][1]),
           'up_atten' : strip_val(values[2][2]),
           'down_noise' : strip_val(values[3][1]),
           'up_noise' : strip_val(values[3][2]) }


def main():
  if (len(sys.argv) > 1):
    try:
      { 'show' : lambda: print_stats(grab_stats()),
        'init' : lambda: rrd_init(),
        'update' : lambda: rrd_update(grab_stats()),
        'generate' : lambda: rrd_generate() }[sys.argv[1]]()
    except KeyError:
      print 'Usage: ' + sys.argv[0] + ' (show|init|update|generate)'
  else:
    print 'Usage: ' + sys.argv[0] + ' (show|init|update|generate)'


if __name__ == '__main__':
  main()

