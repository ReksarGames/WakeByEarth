# Import once. Stop before changing anything if either name already exists.
:if ([:len [/system script find where name="WakeByEarth"]] > 0) do={ :error "WakeByEarth script already exists"; };
:if ([:len [/system scheduler find where name="WakeByEarth"]] > 0) do={ :error "WakeByEarth scheduler already exists"; };
/system script add name=WakeByEarth policy=ftp,read,write,test source={
# WakeByEarth template for RouterOS 6. Configure a *.local.rsc copy before use.
# Read one direct JSON member (or the first array item), preserving JSON scalar types.
:local jsonField do={
    :local json $1;
    :local key $2;
    :local prefix ("\"" . $key . "\":");
    :local depth 0;
    :local quoted false;
    :local escaped false;
    :local array false;
    :local member "";
    :if ([:len $json] = 0) do={ :return ""; };
    :for i from=0 to=([:len $json] - 1) do={
        :local c [:pick $json $i ($i + 1)];
        :if ($quoted) do={
            :set member ($member . $c);
            :if ($escaped) do={
                :set escaped false;
            } else={
                :if ($c = "\\") do={ :set escaped true; } else={
                    :if ($c = "\"") do={ :set quoted false; };
                };
            };
        } else={
            :if ($c = "\"") do={
                :set quoted true;
                :set member ($member . $c);
            } else={
                :if (($c != " ") && ($c != "\r") && ($c != "\n") && ($c != "\t")) do={
                    :if (($c = "{") || ($c = "[")) do={
                        :if ($depth = 0) do={ :set array ($c = "["); } else={
                            :set member ($member . $c);
                        };
                        :set depth ($depth + 1);
                    } else={
                        :if (($depth = 1) && (($c = ",") || ($c = "}") || ($c = "]"))) do={
                            :if ($array) do={ :return $member; };
                            :if ([:pick $member 0 [:len $prefix]] = $prefix) do={
                                :return [:pick $member [:len $prefix] [:len $member]];
                            };
                            :set member "";
                        } else={
                            :set member ($member . $c);
                        };
                        :if (($c = "}") || ($c = "]")) do={ :set depth ($depth - 1); };
                    };
                };
            };
        };
    };
    :return "";
};

:global wolLastOffset;

:local token "YOUR_BOT_TOKEN";
:local chatid "YOUR_TELEGRAM_ID";

:if ([:len $wolLastOffset] = 0) do={
    :set wolLastOffset "0";
};

:local url ("https://api.telegram.org/bot" . $token . "/getUpdates?offset=" . $wolLastOffset . "&limit=1");

:local result [/tool fetch url=$url as-value output=user];
:local body ($result->"data");

:local updates [$jsonField $body "result"];
:local update [$jsonField $updates ""];
:local uid [$jsonField $update "update_id"];

:if (([$jsonField $body "ok"] = "true") && ([:typeof [:tonum $uid]] = "num")) do={
    :set wolLastOffset ([:tonum $uid] + 1);

    /tool fetch \
        url=("https://api.telegram.org/bot" . $token . "/getUpdates?offset=" . $wolLastOffset . "&limit=1") \
        keep-result=no;

    # Check direct sender/chat fields, never IDs inside replies or forwarded messages.
    :local message [$jsonField $update "message"];
    :local sender [$jsonField $message "from"];
    :local chat [$jsonField $message "chat"];
    :local command "";
    :if (([$jsonField $sender "id"] = $chatid) && \
         ([$jsonField $chat "id"] = $chatid) && \
         ([$jsonField $chat "type"] = "\"private\"")) do={
        :set command [$jsonField $message "text"];
    };

    :if ($command = "\"turnon\"") do={

        /tool wol \
            mac=XX:XX:XX:XX:XX:XX \
            interface=bridge;

        /tool fetch \
            url=("https://api.telegram.org/bot" . $token . "/sendMessage?chat_id=" . $chatid . "&text=Wake-on-LAN%20packet%20sent%20successfully.") \
            keep-result=no;
    };

    :if ($command = "\"status\"") do={
        /tool fetch \
            url=("https://api.telegram.org/bot" . $token . "/sendMessage?chat_id=" . $chatid . "&text=Computer%20IP%20is%20not%20configured.") \
            keep-result=no;
    };
    :if ($command = "\"internet\"") do={
        :local received [/ping 8.8.8.8 count=5];
        /tool fetch \
            url=("https://api.telegram.org/bot" . $token . "/sendMessage?chat_id=" . $chatid . "&text=Internet%20check:%20" . $received . "%20of%205%20ping%20replies.") \
            keep-result=no;
    };
}
}
/system scheduler add name=WakeByEarth interval=1m on-event=WakeByEarth policy=ftp,read,write,test
