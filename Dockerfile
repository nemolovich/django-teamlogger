# TeamLogger
# Copyright (C) 2017  Maxence PAPILLON
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

FROM python:3.6

LABEL maintainer=maxence.papillon@outlook.com

# set static and media directories to use
ENV APP_PATH=/usr/src/app
ENV LOGS_PATH=/var/log
ENV APP_STATIC_ROOT=/srv/app/static
ENV APP_MEDIA_ROOT=/srv/app/media
ENV MOD_WSGI_VERSION="4.5.19"

# set application in production mode
ENV DJANGO_SETTINGS_MODULE=teamlogger.settings.production

WORKDIR ${APP_PATH}

EXPOSE 8000
VOLUME ["${LOGS_PATH}", "${APP_PATH}", "${APP_STATIC_ROOT}", "${APP_MEDIA_ROOT}"]

STOPSIGNAL SIGTERM

# get requirements
COPY ./requirements_prod.txt ./requirements.txt ${APP_PATH}/
RUN pip install --no-cache-dir -r requirements_prod.txt

# copy all files into container
COPY ./ ${APP_PATH}/

# create static and media directories
RUN mkdir -p ${APP_STATIC_ROOT} ${APP_MEDIA_ROOT}

# make starting script runable
RUN chmod +x docker-start-server.sh \
  && chmod +x ./httpd/install-apache.sh && ./httpd/install-apache.sh

CMD ["./docker-start-server.sh"]

