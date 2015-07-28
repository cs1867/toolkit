#!/usr/bin/perl

use strict;
use warnings;
use CGI;
use Log::Log4perl qw(get_logger :easy :levels);
use POSIX;
use Data::Dumper;
use JSON::XS;
use XML::Simple;
use Sys::MemInfo qw(totalmem);
use FindBin qw($RealBin);

my $basedir = "$RealBin/../../../";

use lib "$RealBin/../../../../lib";

use perfSONAR_PS::NPToolkit::DataService::Host;
use perfSONAR_PS::NPToolkit::WebService::Method;
use perfSONAR_PS::NPToolkit::WebService::Router;

use Config::General;
use Time::HiRes qw(gettimeofday tv_interval);

# TODO: add check for auth
# TODO: add request method

my $config_file = $basedir . '/etc/web_admin.conf';
my $conf_obj = Config::General->new( -ConfigFile => $config_file );
our %conf = $conf_obj->getall;

if ( $conf{logger_conf} ) {
    unless ( $conf{logger_conf} =~ /^\// ) {
        $conf{logger_conf} = $basedir . "/etc/" . $conf{logger_conf};
    }

    Log::Log4perl->init( $conf{logger_conf} );
}
else {

    # If they've not specified a logger, send it all to /dev/null
    Log::Log4perl->easy_init( { level => $DEBUG, file => "/dev/null" } );
}

our $logger = get_logger( "perfSONAR_PS::WebGUI::ServiceStatus" );
if ( $conf{debug} ) {
    $logger->level( $DEBUG );
}

my $data;
my $host_info = perfSONAR_PS::NPToolkit::DataService::Host->new( { 'config_file' => $config_file  } );

#my $cgi = CGI->new();

my $router = perfSONAR_PS::NPToolkit::WebService::Router->new();

my $summary_method = perfSONAR_PS::NPToolkit::WebService::Method->new(
    name            =>  "get_summary",
    description     =>  "Retrieves host summary",
    callback        =>  sub { $host_info->get_summary(@_); }
    );

$router->add_method($summary_method);

my $info_method = perfSONAR_PS::NPToolkit::WebService::Method->new(
    name            =>  "get_info",
    description     =>  "Retrieves host information",
    callback        =>  sub { $host_info->get_information(@_); }
    );

$router->add_method($info_method);

my $info_update_method = perfSONAR_PS::NPToolkit::WebService::Method->new(
    name            => "update_info",
    description     => "Updates host information",
    auth_required   => 1,
    callback        => sub { $host_info->update_information(@_); },
    min_params      => 1,
    );

$info_update_method->add_input_parameter(
    name            => "organization_name",
    description     => "The name of the organization",
    required        => 0,
    allow_empty     => 1,
    type            => 'text',
    );

$info_update_method->add_input_parameter(
    name            => "admin_name",
    description     => "The name of the administrator",
    required        => 0,
    allow_empty     => 1,
    type            => 'text',
    );

$info_update_method->add_input_parameter(
    name            => "admin_email",
    description     => "The e-mail address of the administrator",
    required        => 0,
    allow_empty     => 1,
    type            => 'text',
    );

$info_update_method->add_input_parameter(
    name            => "city",
    description     => "The city of the administrator or organization",
    required        => 0,
    allow_empty     => 1,
    type            => 'text',
    );

$info_update_method->add_input_parameter(
    name            => "state",
    description     => "The state/province of the administrator or organization",
    required        => 0,
    allow_empty     => 1,
    type            => 'text',
    #min_length      => 2,
    #max_length      => 6,

    );

$info_update_method->add_input_parameter(
    name            => "postal_code",
    description     => "The postal code of the administrator or organization",
    required        => 0,
    allow_empty     => 1,
    type            => 'postal_code',
    );

$info_update_method->add_input_parameter(
    name            => "country",
    description     => "The country of the administrator or organization",
    required        => 0,
    allow_empty     => 1,
    type            => 'text',
    );

$info_update_method->add_input_parameter(
    name            => "latitude",
    description     => "The latitude of the node",
    required        => 0,
    allow_empty     => 1,
    type            => 'float',
    );

$info_update_method->add_input_parameter(
    name            => "longitude",
    description     => "The longitude of the node",
    required        => 0,
    allow_empty     => 1,
    type            => 'float',
    );

$info_update_method->add_input_parameter(
    name            => "subscribe",
    description     => "Whether to subscribe the administrator to the perfsonar user list",
    required        => 0,
    allow_empty     => 1,
    type            => 'boolean',
    );


$router->add_method($info_update_method);

my $status_method = perfSONAR_PS::NPToolkit::WebService::Method->new(
    name            =>  "get_status",
    description     =>  "Retrieves host status information",
    callback        =>  sub { $host_info->get_status(@_); }
    );

$router->add_method($status_method);

my $health_method = perfSONAR_PS::NPToolkit::WebService::Method->new(
    name            => "get_health",
    description     =>  " Retrieves host health information",
    auth_required   => 1,
    callback        => sub {$host_info->get_system_health(@_);}
);

$router->add_method($health_method);

my $services_method = perfSONAR_PS::NPToolkit::WebService::Method->new(
    name            =>  "get_services",
    description     =>  "Retrieves host services information",
    callback        =>  sub { $host_info->get_services(@_); }
    );

$router->add_method($services_method);

my $services_update_method = perfSONAR_PS::NPToolkit::WebService::Method->new(
    name            => "update_enabled_services",
    description     => "Updates enabled service configuration",
    auth_required   => 1,
    callback        => sub { $host_info->update_enabled_services(@_); },
    min_params      => 1,
    );

$services_update_method->add_input_parameter(
    name            => "bwctl",
    description     => "Whether to enable the BWCTL service",
    required        => 0,
    type            => 'boolean',
    );

$services_update_method->add_input_parameter(
    name            => "owamp",
    description     => "Whether to enable the OWAMP service",
    required        => 0,
    type            => 'boolean',
    );

$services_update_method->add_input_parameter(
    name            => "ndt",
    description     => "Whether to enable the NDT service",
    required        => 0,
    type            => 'boolean',
    );

$services_update_method->add_input_parameter(
    name            => "npad",
    description     => "Whether to enable the NPAD service",
    required        => 0,
    type            => 'boolean',
    );

$router->add_method($services_update_method);

my $communities_method = perfSONAR_PS::NPToolkit::WebService::Method->new(
    name            =>  "get_communities",
    description     =>  "Retrieves host communities information",
    callback        =>  sub { $host_info->get_communities(@_); }
    );

$router->add_method($communities_method);

#TODO: more testing on the get_all_communities method
my $all_communities_method = perfSONAR_PS::NPToolkit::WebService::Method->new(
    name            =>  "get_all_communities",
    description     =>  "Retrieves all available communities",
    callback        =>  sub { $host_info->get_all_communities(@_); }
    );

$router->add_method($all_communities_method);

my $meshes_method = perfSONAR_PS::NPToolkit::WebService::Method->new(
    name            =>  "get_meshes",
    description     =>  "Retrieves host mesh information",
    callback        =>  sub { $host_info->get_meshes(@_); }
    );

$router->add_method($meshes_method);

$router->handle_request();

# vim: expandtab shiftwidth=4 tabstop=4
