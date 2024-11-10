FROM fluent/fluentd:v1.16.5-1.0

USER root

RUN gem install fluent-plugin-elasticsearch --no-document --version 5.4.3 \
    && gem sources --clear-all

RUN gem install elasticsearch-xpack --version 7.17.11 \
    && gem sources --clear-all \
    && rm -rf /tmp/* /var/tmp/* /usr/lib/ruby/gems/*/cache/*.gem

RUN gem install fluent-plugin-prometheus --version 2.1.0 \
    && gem sources --clear-all \
    && rm -rf /tmp/* /var/tmp/* /usr/lib/ruby/gems/*/cache/*.gem

RUN gem install fluent-plugin-json --no-document \
    && gem sources --clear-all \
    && rm -rf /tmp/* /var/tmp/* /usr/lib/ruby/gems/*/cache/*.gem

USER fluent