#!/usr/bin/php
<?php

// Am using php for this because Perl's Net::RabbitMQ intermittently (and very often) generated
// "frame read error" errors (or words to that effect) when trying to consume from the queue. I
// couldnt' figure out why, but that made it very unreliable.


namespace
  {
    print "WORKER STDOUT\n";
    error_log("WORKER STDERR");

    // define this so that the callbacks from the service proiders get the proper versioned path to the callback endpoint:
    define ('KREST_ENDPOINT_PATH_PREFIX', '/v1');

    $parent_dir = dirname(__DIR__);
    set_include_path("$parent_dir/lib:".get_include_path());
    require_once 'ClassAutoloader.php';
    require_once "$parent_dir/vendor/autoload.php";

    use PhpAmqpLib\Connection\AMQPStreamConnection;
    use PhpAmqpLib\Message\AMQPMessage;


    $provider_key = 'sinch';
    $provider_keyword = Config::Get("RabbitMQ/sms/providers/$provider_key/keyword");
    $providerID = \Provider::GetID($provider_keyword);

    $MB_queue_name          = Config::Get("RabbitMQ/sms/providers/$provider_key/queue_name");
    $MB_host                = Config::Get('RabbitMQ/host');
    $MB_port                = Config::Get('RabbitMQ/port');
    $MB_heartbeat_interval  = Config::GetOptional('RabbitMQ/heartbeat_interval') ?? 0;
    $MB_user                = Config::Get('RabbitMQ/sms/consume_user');
    $MB_pass                = Config::Get('RabbitMQ/sms/consume_pass');
    $MB_vhost               = Config::Get('RabbitMQ/sms/vhost');

    while (1)
      {
        try
          {
            print "Connecting to database\n";
            $db = DBH::RW();
            print "Connected to database\n";

            print "Connecting to $MB_host, vhost=$MB_vhost\n";
            $MQconnection = new AMQPStreamConnection
              (
                host:       $MB_host,
                port:       $MB_port,
                user:       $MB_user,
                password:   $MB_pass,
                vhost:      $MB_vhost,
                heartbeat:  $MB_heartbeat_interval,
                keepalive:  true
              );
            print "Connected to $MB_host, vhost=$MB_vhost\n";

            $channel = $MQconnection->channel();
            $channel->basic_qos
              (
                prefetch_size:  0,
                prefetch_count: 1,
                a_global:       false
              );

            $message_handler = function (\PhpAmqpLib\Message\AMQPMessage $msg) use ($db)
              { return submitSMS($db, $msg); };

            $channel->basic_consume
              (
                queue:        $MB_queue_name,
                consumer_tag: '',
                no_local:     false,
                no_ack:       false,
                exclusive:    false,
                nowait:       false,
                callback:     $message_handler,
                ticket:       NULL,
                arguments:
                  [
                    //'count' => 1,
                  ]
              );

            print "Consuming RabbitMQ queue $MB_queue_name\n";
            $channel->consume();
            print "Finished consuming from RabbitMQ\n";
          }

        catch (\Exception $e)
          {
            error_log("Caught ".get_class($e).": ".$e->getMessage());
            sleep(10);
          }
      }


    $channel->close();
    $MQconnection->close();


    // function barf(string $msg)
    //   { throw new \Exception($msg); }


    function submitSMS(\DBO $db, \PhpAmqpLib\Message\AMQPMessage $MBmsg)
      {
        $msgstruct = NULL;

        try
          {
            $db->beginTransaction();
            echo date('H:i:s').'  received ', $MBmsg->body, "\n";

            $msg = new \MsgQtoSMSC\MsgOutParsed($MBmsg->body);

            # get the records locked to this transaction:
            $recipIDs = $msg->recipIDs;
            $recipIDCSVQ = $db->quoteListCSV($recipIDs);
            $lockedIDs = $db->selectAllColumn("SELECT ID FROM message_out_recipients WHERE ID IN ($recipIDCSVQ) FOR UPDATE");
            if (count($lockedIDs) !== count($recipIDs))
              { throw new TempError(sprintf("Failed to lock all rows; expected %d but locked %d", count($recipIDs), count($lockedIDs))); }

            $submit_res = \LibSMS\Message::SubmitToSMSC
              (
                from:               $msg->from,
                to:                 $msg->to,
                body:               $msg->body,
                internal_messageID: $msg->internal_messageID,
                clusterID:          $msg->clusterID,
                expires_at:         $msg->expires_at
              );

            if (!$submit_res)
              {
                $db->rollback();
                error_log("Failed to submit SMS message to SMSC");
                return false;
              }

            $query = "UPDATE message_out_recipients SET ".
                        "status='submitted',".
                        "statusCode=102,".
                        "submitted_at_ms=UNIX_TIMESTAMP_MS(),".
                        "service_providerID=?,".
                        "provider_messageID=? ".
                      "WHERE messageID=? ".
                      "AND status IN ('queued','pending') ". # should never be pending, but just in case that bit went wrong
                      "AND ID IN ($recipIDCSVQ)";
            $db->exec($query, $submit_res['service_providerID'], $submit_res['provider_messageID'], $msg->internal_messageID);

            $MBmsg->ack(multiple: false);
            $db->commit();
          }

        catch (MsgQtoSMSC\TempError $e)
          {
            $db->rollback();
            error_log("Temp sms submit failure: ".$e->getMessage());
          }


        catch (MsgQtoSMSC\PermError $e)
          {
            $db->rollback();
            error_log("Permanent sms submit failure: ".$e->getMessage());
            error_log("Need to write to failure queue, or something");
            $MBmsg->ack(multiple: false);
          }


        catch (Exception $e)
          {
            $db->rollback();
            error_log("Error submitting message: ".$e->getMessage());
          }


      }
  } // namespace


namespace MsgQtoSMSC
  {
    class MsgOutParsed
      {
        private $props = [];

        public function __construct(string $json_src)
          {
            try
              {
                $struct = json_decode
                  (
                    $json_src,
                    associative:  false,
                    flags:        JSON_THROW_ON_ERROR
                  );
              }
            catch (\Exception $e)
              { throw new PermError("Unable to decode message: ".$e->getMessage()."\nBODY=$json_src"); }

            foreach (['internal_messageID','type','direction','from','to','body','clusterID','recipIDs','expires_at'] as $reqprop)
              {
                if (!isset($struct->$reqprop))
                  { throw new PermError(get_class().": src property missing or not set: $reqprop"); }
              }

            if ($struct->type !== 'sms')
              { throw new PermError("Message type is not 'sms'; it is '{$struct->type}'"); }

            if ($struct->direction !== 'out')
              { throw new PermError("Message direction is not 'out'; it is '{$struct->direction}'"); }

            foreach (['internal_messageID','clusterID'] as $intprop)
              {
                if (!is_numeric($struct->$intprop) || !preg_match('/^[0-9]+$/', $struct->$intprop))
                  { throw new PermError(get_class().": src property $intprop non-valid: {$struct->$intprop}"); }
              }
 
            foreach (['to','recipIDs'] as $non_empty_arrayprop)
              {
                if (!is_array($struct->$non_empty_arrayprop))
                  { throw new PermError(get_class().": src property $non_empty_arrayprop is not an array"); }
                if (empty($struct->$non_empty_arrayprop))
                  { throw new PermError(get_class().": src property $non_empty_arrayprop is empty"); }
              }
 
            foreach ($struct->recipIDs as $recipID)
              {
                if (!preg_match('/^[0-9]+$/', $recipID))
                  { throw new PermError("Non-valid recipID in source data: $recipID"); }
              }

            try
              {
                foreach ($struct->to as $i=>&$recip)
                  { $recip = new \TelNum($recip); }
              }
            catch (\Exception $e)
              { throw new PermError("Bad recipient number at offset $i: $recip"); }

            try
              { $struct->expires_at = new \Timestamp($struct->expires_at); }
            catch (\Exception $e)
              {
                error_log("Bad src struct: ".print_r($struct,1));
                throw new PermError("Bad expires_at value: {$struct->expires_at}");
              }

            $this->props = (array) $struct;
          }

        public function __get($prop)
          {
            if (($val = $this->props[$prop] ?? NULL) !== NULL)
              { return $val; }
            if (array_key_exists($prop, $this->props))
              { return NULL; }
            throw new \Exception("No such property: ".get_class($this)."->$prop");
          }
      }


    class TempError extends \Exception
      {
      }


    class PermError extends \Exception
      {
      }

  }

